import 'dart:convert';
import 'package:flutter/services.dart';

enum Role { athlete, coach, superuser }

extension RoleLabel on Role {
  String get label => switch (this) {
        Role.athlete => 'Atleta',
        Role.coach => 'Coach',
        Role.superuser => 'Superuser',
      };
}

class Workout {
  final int id;
  final DateTime date;
  final int order;
  final String name;
  final String description;
  final List<RangeGroup> ranges;
  final String audience; // all | assigned | personal
  final List<EditorLine>? lines; // righe strutturate (nuovo editor); null per i workout legacy
  Workout({
    required this.id,
    required this.date,
    required this.order,
    required this.name,
    required this.description,
    required this.ranges,
    this.audience = 'all',
    this.lines,
  });

  factory Workout.fromJson(Map<String, dynamic> j) => Workout(
        id: j['id'],
        date: DateTime.parse(j['date']),
        order: j['order'],
        name: j['name'],
        description: j['description'],
        ranges: (j['ranges'] as List)
            .map((r) => RangeGroup(r['exercise'], (r['values'] as List).cast<int>()))
            .toList(),
      );

  String get format {
    final n = name.toLowerCase();
    if (n.startsWith('emom')) return 'EMOM';
    if (n.startsWith('amrap')) return 'AMRAP';
    if (n.contains('for time')) return 'FOR TIME';
    if (n.startsWith('ev.') || n.startsWith('every')) return 'EVERY';
    if (n.contains('hiit') || n.contains('conditioning') || n.contains('mono')) return 'CONDITIONING';
    if (ranges.isNotEmpty) return 'FORZA';
    return 'LIBERO';
  }
}

class RangeGroup {
  final String exercise;
  final List<int> values;
  RangeGroup(this.exercise, this.values);
}

class MaxRecord {
  final String exercise;
  final DateTime date;
  final double value;
  final String unit;
  final String testType;
  final String test; // distanza o variante del test: '', '500m', '2k', ...
  MaxRecord(this.exercise, this.date, this.value, {this.unit = 'kg', this.testType = '1RM', this.test = ''});
  String get key => test.isEmpty ? exercise : '$exercise $test';
}

class Score {
  final int workoutId;
  final String athlete;
  final String result;
  final bool rx;
  final int sortKey;
  Score(this.workoutId, this.athlete, this.result, {this.rx = true, this.sortKey = 0});
}

class Athlete {
  final String name;
  final String username;
  final bool enabled;
  final int lastSeenDays;
  final int workouts30;
  final String trend; // up | flat | down
  Athlete(this.name, this.username, {this.enabled = true, this.lastSeenDays = 0, this.workouts30 = 0, this.trend = 'flat'});
}

class Message {
  final String title;
  final String body;
  final DateTime date;
  final bool pinned;
  bool read;
  Message(this.title, this.body, this.date, {this.pinned = false, this.read = false});
}

class LogEntry {
  final DateTime at;
  final String user;
  final String role;
  final String action;
  final String target;
  LogEntry(this.at, this.user, this.role, this.action, this.target);
}


/// Riga strutturata di un allenamento: esercizio dal catalogo, testo libero o intestazione di blocco.
class EditorLine {
  String kind; // exercise | text | block
  CatalogExercise? exercise;
  String freeText;
  String qty; // es. "5", "400", "12+12"
  String qtyUnit; // reps | m | cal | sec | min
  String loadKind; // none | kg | pct | offset | zone
  String loadValue;
  String refTest; // test di riferimento per la percentuale: '' (1RM), '500m', '2k', ...
  String cadence; // ritmo di palata / pedalata, es. "20-22"
  String note;
  bool inBlock; // la riga appartiene al blocco che la precede
  int setsMin, setsMax; // solo per kind = block
  EditorLine({
    this.kind = 'text',
    this.exercise,
    this.freeText = '',
    this.qty = '',
    this.qtyUnit = 'reps',
    this.loadKind = 'none',
    this.loadValue = '',
    this.refTest = '',
    this.cadence = '',
    this.note = '',
    this.inBlock = false,
    this.setsMin = 3,
    this.setsMax = 3,
  }) {
    if (exercise != null) kind = 'exercise';
  }

  bool get isBlock => kind == 'block';
  bool get isFree => !isBlock && exercise == null;

  String render() {
    if (isBlock) return setsMin == setsMax ? '$setsMin giri di:' : '$setsMin–$setsMax giri di:';
    if (isFree) return freeText;
    final b = StringBuffer();
    if (qty.isNotEmpty) {
      b.write(switch (qtyUnit) { 'reps' => '$qty ', 'min' => "$qty' ", 'sec' => '$qty" ', _ => '$qty$qtyUnit ' });
    }
    b.write(exercise!.name);
    switch (loadKind) {
      case 'kg':
        b.write(' $loadValue kg');
      case 'pct':
        b.write(' $loadValue%${refTest.isNotEmpty ? ' del test $refTest' : ''}');
      case 'offset':
        b.write(' +${loadValue}s${refTest.isNotEmpty ? ' sul test $refTest' : ''}');
      case 'zone':
        b.write(' Z$loadValue');
    }
    if (cadence.isNotEmpty) b.write(' · $cadence s/m');
    if (note.isNotEmpty) b.write(' ($note)');
    return b.toString();
  }
}

class CatalogExercise {
  final String name, category, unit;
  final List<String> aliases;
  CatalogExercise(this.name, this.category, this.unit, this.aliases);
  String get categoryLabel => switch (category) {
        'weightlifting' => 'Pesistica',
        'monostructural' => 'Monostrutturale',
        'bodyweight' => 'Corpo libero',
        _ => 'Skill',
      };
}

List<String> _csvSplit(String line) {
  final out = <String>[];
  final b = StringBuffer();
  var q = false;
  for (var i = 0; i < line.length; i++) {
    final c = line[i];
    if (c == '"') {
      if (q && i + 1 < line.length && line[i + 1] == '"') { b.write('"'); i++; } else { q = !q; }
    } else if (c == ',' && !q) { out.add(b.toString()); b.clear(); } else { b.write(c); }
  }
  out.add(b.toString());
  return out;
}

class DemoData {
  static List<Workout> workouts = [];
  static List<CatalogExercise> catalog = [];
  static int _nextId = 100000;
  static int nextId() => _nextId++;

  static Future<void> loadCatalog() async {
    final raw = await rootBundle.loadString('assets/catalogo.csv');
    final lines = raw.split('\n').where((l) => l.trim().isNotEmpty).toList();
    catalog = [
      for (final l in lines.skip(1))
        () { final f = _csvSplit(l); return CatalogExercise(f[0], f[1], f[2], f[6].split(';').where((a) => a.isNotEmpty).toList()); }(),
    ];
  }

  static CatalogExercise? matchExercise(String text) {
    final t = text.toLowerCase().replaceAll(RegExp(r'\s+'), ' ').trim();
    if (t.isEmpty) return null;
    CatalogExercise? best; var bestLen = 0;
    for (final e in catalog) {
      for (final k in [e.name.toLowerCase(), ...e.aliases]) {
        if (k.length > bestLen && t.contains(k)) { best = e; bestLen = k.length; }
      }
    }
    return best;
  }
  static final DateTime today = DateTime(2026, 9, 17);

  static Future<void> load() async {
    final raw = await rootBundle.loadString('assets/workouts.json');
    final list = (jsonDecode(raw) as List).map((e) => Workout.fromJson(e)).toList();
    workouts = list;
    await loadCatalog();
    // Allenamento dedicato e personale di esempio
    final row = catalog.firstWhere((e) => e.name == 'Row');
    final mono = [
      EditorLine(exercise: row, qty: '5', qtyUnit: 'min', loadKind: 'zone', loadValue: '2'),
      EditorLine(kind: 'block', setsMin: 3, setsMax: 4),
      EditorLine(exercise: row, qty: '4', qtyUnit: 'min', loadKind: 'pct', loadValue: '95', refTest: '2k', cadence: '20-22', inBlock: true),
      EditorLine(exercise: row, qty: '1', qtyUnit: 'min', loadKind: 'pct', loadValue: '85', refTest: '2k', note: 'active rest', inBlock: true),
    ];
    workouts.add(Workout(
      id: 90000,
      date: DateTime(2026, 9, 17),
      order: 60,
      name: 'Monostructural',
      description: mono.map((l) => l.render()).join('\n'),
      ranges: [],
      lines: mono,
    ));
    workouts.add(Workout(
      id: 90001,
      date: DateTime(2026, 9, 17),
      order: 99,
      name: 'Recupero spalla',
      description: '3 giri\n12 Banded Face Pull\n10 Ring Row (tempo 3.1.X.1)\n30" Dead Hang',
      ranges: [],
      audience: 'assigned',
    ));
    workouts.add(Workout(
      id: 90002,
      date: DateTime(2026, 9, 17),
      order: 100,
      name: 'Riscaldamento anche',
      description: '2 giri\n10 Kang Squat\n10+10 Cossack Squat\n20" Psoas March',
      ranges: [],
      audience: 'personal',
    ));
    workouts.add(Workout(
      id: 90003,
      date: DateTime(2026, 9, 19),
      order: 100,
      name: 'Riscaldamento anche',
      description: '2 giri\n10 Kang Squat\n10+10 Cossack Squat\n20" Psoas March',
      ranges: [],
      audience: 'personal',
    ));
  }

  static List<Workout> forDay(DateTime d) {
    final l = workouts.where((w) => w.date.year == d.year && w.date.month == d.month && w.date.day == d.day).toList();
    l.sort((a, b) {
      final ra = a.audience == 'all' ? 0 : (a.audience == 'assigned' ? 1 : 2);
      final rb = b.audience == 'all' ? 0 : (b.audience == 'assigned' ? 1 : 2);
      if (ra != rb) return ra - rb;
      return a.order != b.order ? a.order - b.order : a.id - b.id;
    });
    return l;
  }

  // Massimali dell'atleta demo, con storico
  static final List<MaxRecord> maxRecords = [
    MaxRecord('Back Squat', DateTime(2026, 1, 12), 110),
    MaxRecord('Back Squat', DateTime(2026, 4, 3), 117.5),
    MaxRecord('Back Squat', DateTime(2026, 7, 21), 122.5),
    MaxRecord('Front Squat', DateTime(2026, 2, 2), 95),
    MaxRecord('Front Squat', DateTime(2026, 6, 15), 100),
    MaxRecord('Deadlift', DateTime(2026, 1, 20), 140),
    MaxRecord('Deadlift', DateTime(2026, 5, 11), 150),
    MaxRecord('Deadlift', DateTime(2026, 8, 30), 155),
    MaxRecord('Squat Snatch', DateTime(2026, 3, 9), 62.5),
    MaxRecord('Squat Snatch', DateTime(2026, 7, 7), 67.5),
    MaxRecord('Squat Clean', DateTime(2026, 3, 9), 82.5),
    MaxRecord('Squat Clean', DateTime(2026, 8, 12), 87.5),
    MaxRecord('Power Snatch', DateTime(2026, 4, 20), 57.5),
    MaxRecord('Bench Press', DateTime(2026, 2, 17), 80),
    MaxRecord('Bench Press', DateTime(2026, 6, 29), 85),
    MaxRecord('Push Press', DateTime(2026, 5, 5), 65),
    MaxRecord('Clean & Jerk', DateTime(2026, 6, 1), 85),
    MaxRecord('Row', DateTime(2026, 3, 30), 1.72, unit: 'pace', testType: 'Pace', test: '500m'),
    MaxRecord('Row', DateTime(2026, 8, 4), 1.68, unit: 'pace', testType: 'Pace', test: '500m'),
    MaxRecord('Row', DateTime(2026, 4, 14), 7.58, unit: 'min', testType: 'Tempo', test: '2k'),
    MaxRecord('Row', DateTime(2026, 9, 1), 7.3334, unit: 'min', testType: 'Tempo', test: '2k'),
    MaxRecord('Run', DateTime(2026, 5, 18), 4.25, unit: 'min', testType: 'Tempo', test: '1k'),
    MaxRecord('Pull-up', DateTime(2026, 4, 1), 18, unit: 'reps', testType: 'Max reps'),
    MaxRecord('Pull-up', DateTime(2026, 8, 20), 22, unit: 'reps', testType: 'Max reps'),
    MaxRecord('Bar Muscle-up', DateTime(2026, 7, 1), 6, unit: 'reps', testType: 'Max reps'),
    MaxRecord('Dips', DateTime(2026, 2, 10), 20, unit: 'reps', testType: 'Max reps'),
  ];

  static MaxRecord? currentMax(String exercise) {
    final l = maxRecords.where((m) => m.key.toLowerCase() == exercise.toLowerCase()).toList();
    if (l.isEmpty) return null;
    l.sort((a, b) => a.date.compareTo(b.date));
    return l.last;
  }

  static List<MaxRecord> history(String exercise) {
    final l = maxRecords.where((m) => m.key == exercise).toList();
    l.sort((a, b) => a.date.compareTo(b.date));
    return l;
  }


  static const int maxHr = 190;
  static const zoneBounds = [50, 60, 70, 80, 90, 100];

  static int testMeters(String t) {
    final m = RegExp(r'^(\d+(?:\.\d+)?)(k|m)$').firstMatch(t.toLowerCase().replaceAll(' ', ''));
    if (m == null) return 0;
    final v = double.parse(m.group(1)!);
    return (m.group(2) == 'k' ? v * 1000 : v).round();
  }

  static int refMeters(String exercise) => (exercise == 'Row' || exercise == 'Ski Erg') ? 500 : 1000;

  /// Passo di riferimento in secondi (per 500m o per km) ricavato dal test indicato.
  static double? basePace(String exercise, String test) {
    final recs = maxRecords.where((m) => m.exercise == exercise && (test.isEmpty || m.test.toLowerCase() == test.toLowerCase())).toList();
    if (recs.isEmpty) return null;
    recs.sort((a, b) => a.date.compareTo(b.date));
    final r = recs.last;
    if (r.unit == 'pace') return r.value * 60;
    if (r.unit == 'min') {
      final d = testMeters(r.test);
      if (d == 0) return null;
      return r.value * 60 / (d / refMeters(exercise));
    }
    return null;
  }

  static String fmtPace(double sec, String exercise) {
    final s = sec.round();
    return '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')} ${refMeters(exercise) == 500 ? '/500m' : '/km'}';
  }

  /// Valore personalizzato da mostrare all'atleta per una riga; null se non applicabile.
  static String? computed(EditorLine l) {
    if (l.exercise == null) return null;
    final ex = l.exercise!;
    if (l.loadKind == 'zone') {
      final z = int.tryParse(l.loadValue) ?? 0;
      if (z < 1 || z > 5) return null;
      return '${(maxHr * zoneBounds[z - 1] / 100).round()}–${(maxHr * zoneBounds[z] / 100).round()} bpm';
    }
    final v = double.tryParse(l.loadValue.replaceAll(',', '.'));
    if (v == null || v == 0) return null;
    if (ex.unit == 'kg' || ex.category == 'weightlifting') {
      if (l.loadKind != 'pct') return null;
      final m = currentMax(ex.name);
      return m == null ? missing : fmtKg(m.value * v / 100);
    }
    if (ex.unit == 'pace' || ex.unit == 'min') {
      final base = basePace(ex.name, l.refTest);
      if (l.loadKind == 'pct') return base == null ? missing : fmtPace(base * 100 / v, ex.name);
      if (l.loadKind == 'offset') return base == null ? missing : fmtPace(base + v, ex.name);
    }
    if (ex.unit == 'reps' && l.loadKind == 'pct') {
      final m = currentMax(ex.name);
      return m == null ? missing : '${(m.value * v / 100).round()} reps';
    }
    return null;
  }

  static const missing = 'test mancante';

  static List<String> testsFor(String exercise) {
    final have = maxRecords.where((m) => m.exercise == exercise && m.test.isNotEmpty).map((m) => m.test).toSet().toList();
    for (final d in ['500m', '1k', '2k', '5k']) {
      if (!have.contains(d)) have.add(d);
    }
    return have;
  }

  static const Map<String, String> category = {
    'Back Squat': 'Pesistica', 'Front Squat': 'Pesistica', 'Deadlift': 'Pesistica', 'Squat Snatch': 'Pesistica',
    'Squat Clean': 'Pesistica', 'Power Snatch': 'Pesistica', 'Bench Press': 'Pesistica', 'Push Press': 'Pesistica',
    'Clean & Jerk': 'Pesistica', 'Row 500m': 'Monostrutturali', 'Row 2k': 'Monostrutturali', 'Run 1k': 'Monostrutturali',
    'Pull-up': 'Corpo libero', 'Bar Muscle-up': 'Corpo libero', 'Dips': 'Corpo libero',
  };

  static final List<Score> scores = [
    Score(0, 'Biagio', '', sortKey: 0),
  ];

  static List<Score> leaderboard(Workout w) {
    final names = ['Marina M.', 'Vincenzo A.', 'Erica R.', 'Luca P.', 'Sara T.', 'Giorgio F.'];
    final f = w.format;
    final out = <Score>[];
    for (var i = 0; i < names.length; i++) {
      final seed = (w.id * 7 + i * 13) % 97;
      String r;
      int k;
      if (f == 'AMRAP' || f == 'EMOM') {
        final rounds = 5 + seed % 6, reps = seed % 15;
        r = '$rounds round + $reps';
        k = -(rounds * 100 + reps);
      } else if (f == 'FOR TIME' || f == 'CONDITIONING') {
        final s = 540 + seed * 7;
        r = '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')}';
        k = s;
      } else {
        final kg = 60 + seed;
        r = '$kg kg';
        k = -kg;
      }
      out.add(Score(w.id, names[i], r, rx: i % 4 != 3, sortKey: k));
    }
    out.sort((a, b) => (a.rx == b.rx) ? a.sortKey.compareTo(b.sortKey) : (a.rx ? -1 : 1));
    return out;
  }

  static final List<Athlete> athletes = [
    Athlete('Marina Melluso', 'Mellux', lastSeenDays: 0, workouts30: 18, trend: 'up'),
    Athlete('Vincenzo Augella', 'VinAug', lastSeenDays: 6, workouts30: 9, trend: 'flat'),
    Athlete('Erica Rossi', 'Erica', lastSeenDays: 1, workouts30: 15, trend: 'up'),
    Athlete('Luca Perri', 'lucap', lastSeenDays: 21, workouts30: 2, trend: 'down'),
    Athlete('Sara Tomei', 'sarat', lastSeenDays: 2, workouts30: 12, trend: 'flat'),
    Athlete('Giorgio Fini', 'gfini', enabled: false, lastSeenDays: 0, workouts30: 0),
  ];

  static final List<Message> messages = [
    Message('Orari sabato 19', 'Sabato il box apre alle 9:00 e chiude alle 13:00. Unica classe alle 10:00.', DateTime(2026, 9, 16, 18, 30), pinned: true),
    Message('Test 1RM Back Squat', 'Lunedì 21 apriamo il ciclo con il test del Back Squat. Arrivate riposati e con le scarpe giuste.', DateTime(2026, 9, 15, 9, 0)),
    Message('Nuovo ciclo di forza', 'Da questa settimana le percentuali salgono del 3%. Chi non ha i massimali aggiornati li registri entro venerdì.', DateTime(2026, 9, 13, 20, 15), read: true),
  ];

  static final List<LogEntry> log = [
    LogEntry(DateTime(2026, 9, 17, 7, 42), 'Mellux', 'atleta', 'performance_created', 'Emom 9\' del 17/09'),
    LogEntry(DateTime(2026, 9, 17, 7, 40), 'Mellux', 'atleta', 'session_saved', 'Sessione cardio 24:12, FC media 156'),
    LogEntry(DateTime(2026, 9, 16, 22, 5), 'COACH VALE', 'coach', 'workout_published', 'Settimana 14–20 settembre'),
    LogEntry(DateTime(2026, 9, 16, 18, 30), 'COACH VALE', 'coach', 'message_sent', 'Orari sabato 19 → 23 atleti'),
    LogEntry(DateTime(2026, 9, 16, 11, 57), 'Mellux', 'atleta', 'login_ok', 'Android · Tab A9 Pro'),
    LogEntry(DateTime(2026, 9, 15, 19, 20), 'COACH VALE', 'coach', 'invitation_sent', 'giorgio.fini@example.it'),
    LogEntry(DateTime(2026, 9, 15, 16, 29), 'biscarci', 'superuser', 'role_changed', 'VALERIO: atleta → coach'),
    LogEntry(DateTime(2026, 9, 14, 8, 10), 'Erica', 'atleta', 'max_record_created', 'Pull-up 22 reps'),
    LogEntry(DateTime(2026, 9, 13, 20, 15), 'COACH VALE', 'coach', 'message_sent', 'Nuovo ciclo di forza → 23 atleti'),
    LogEntry(DateTime(2026, 9, 12, 9, 3), 'lucap', 'atleta', 'login_failed', '3 tentativi'),
    LogEntry(DateTime(2026, 9, 11, 15, 56), 'VinAug', 'atleta', 'performance_updated', 'For Time del 10/09 · 12:41 → 12:38'),
  ];

  static const motivational = [
    'SÌ VOLA', 'PAZZESCO !', 'TUTTO NELLA SERENITÀ', 'NON MOLLARE', 'STRINGI I DENTI',
    'ANCORA UNO', 'QUI SI SPINGE', 'ZERO SCUSE', 'FINO IN FONDO', 'IL FERRO PESA UGUALE PER TUTTI',
    'SE TREMI STAI FUNZIONANDO', 'LA FATICA NON UCCIDE. IL DIVANO SÌ', 'JUST WORK NOT PLAY',
  ];
  static const restDay = [
    "REST IND' O' LIET", 'OGGI WORKOUT? NO. REST', 'PESI FERMI. BESTIA IN RICARICA',
    'RIPOSO STRATEGICO', 'OGGI RIPOSO PERCHÉ SONO GROSSO, NON SCEMO', 'REST DAY SACRO',
  ];
}

const weekdaysShort = ['L', 'M', 'M', 'G', 'V', 'S', 'D'];
const weekdaysLong = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'];
const monthsLong = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];

String fmtDateLong(DateTime d) => '${weekdaysLong[d.weekday - 1]} ${d.day} ${monthsLong[d.month - 1]}';
String fmtDateShort(DateTime d) => '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}';
String fmtDateMed(DateTime d) => '${d.day} ${monthsLong[d.month - 1].substring(0, 3)} ${d.year}';

String fmtValue(MaxRecord m) {
  switch (m.unit) {
    case 'pace':
      final s = (m.value * 60).round();
      return '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')} /500m';
    case 'min':
      final s = (m.value * 60).round();
      return '${s ~/ 60}:${(s % 60).toString().padLeft(2, '0')}';
    case 'reps':
      return '${m.value.toInt()} reps';
    default:
      return m.value % 1 == 0 ? '${m.value.toInt()} kg' : '${m.value.toStringAsFixed(1).replaceAll('.', ',')} kg';
  }
}

String fmtKg(double v) {
  final r = (v * 2).round() / 2; // arrotonda a 0,5
  return r % 1 == 0 ? '${r.toInt()} kg' : '${r.toStringAsFixed(1).replaceAll('.', ',')} kg';
}
