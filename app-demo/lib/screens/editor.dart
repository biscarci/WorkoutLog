import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';
import '../main.dart';

const categories = ['Forza', 'Metcon', 'Skill', 'Monostrutturale', 'Mobilità', 'Benchmark', 'Test', 'Altro'];
const formats = ['AMRAP', 'For time', 'EMOM', 'Every X min', 'Tabata', 'Sets × reps', 'Libero'];
const resultTypes = ['Tempo', 'Round + reps', 'Carico', 'Ripetizioni', 'Distanza', 'Calorie', 'Nessuno'];

/// Interpreta una riga di testo (formato del coach) in una riga strutturata.
EditorLine lineFromText(String raw, {String? titleHint}) {
  final t = raw.trim();
  final ex = DemoData.matchExercise(t);

  // intestazione di blocco: "3 To 4 Sets", "5 Rounds", "3 giri"
  final blk = RegExp(r'^(\d+)(?:\s*(?:to|-|–)\s*(\d+))?\s*(sets?|rounds?|giri)\b', caseSensitive: false).firstMatch(t);
  if (blk != null && ex == null) {
    final a = int.parse(blk.group(1)!);
    final b = blk.group(2) != null ? int.parse(blk.group(2)!) : a;
    return EditorLine(kind: 'block', setsMin: a, setsMax: b);
  }

  var exercise = ex;
  if (exercise == null && t.contains('%') && titleHint != null) exercise = DemoData.matchExercise(titleHint);
  if (exercise == null) return EditorLine(freeText: t);

  final l = EditorLine(exercise: exercise);
  final body = t.replaceFirst(RegExp(r'^[A-F]\)?\s+'), '');
  final mins = RegExp(r"^(\d+)\s*[’'′](?!\d)").firstMatch(body);
  final secs = RegExp(r'^(\d+)\s*[”"″]').firstMatch(body);
  if (mins != null) {
    l.qty = mins.group(1)!;
    l.qtyUnit = 'min';
  } else if (secs != null) {
    l.qty = secs.group(1)!;
    l.qtyUnit = 'sec';
  } else {
    final q = RegExp(r'^(\d+(?:\+\d+)?)(?:/\d+)?\s*(m|cal)?\b', caseSensitive: false).firstMatch(body);
    if (q != null) {
      l.qty = q.group(1)!;
      l.qtyUnit = (q.group(2) ?? 'reps').toLowerCase();
    }
  }
  final zone = RegExp(r'\bZ([1-5])\b', caseSensitive: false).firstMatch(t);
  final pct = RegExp(r'(\d+)\s*%').firstMatch(t);
  final kg = RegExp(r'(\d+(?:[.,]\d+)?)\s*(?:/\s*\d+(?:[.,]\d+)?)?\s*kg', caseSensitive: false).firstMatch(t);
  if (zone != null) {
    l.loadKind = 'zone';
    l.loadValue = zone.group(1)!;
  } else if (pct != null) {
    l.loadKind = 'pct';
    l.loadValue = pct.group(1)!;
  } else if (kg != null) {
    l.loadKind = 'kg';
    l.loadValue = kg.group(1)!;
  }
  final test = RegExp(r'test\s+(\d+(?:\.\d+)?)\s*(k|m)\b', caseSensitive: false).firstMatch(t);
  if (test != null) l.refTest = '${test.group(1)}${test.group(2)!.toLowerCase()}';
  final cad = RegExp(r'(\d+\s*-\s*\d+)\s*s/m', caseSensitive: false).firstMatch(t);
  if (cad != null) l.cadence = cad.group(1)!.replaceAll(' ', '');
  if (RegExp(r'active rest', caseSensitive: false).hasMatch(t)) l.note = 'active rest';
  return l;
}

/// Interpreta più righe gestendo i blocchi: le righe dopo un'intestazione di blocco ne fanno parte.
List<EditorLine> linesFromText(Iterable<String> rows, {String? titleHint}) {
  final out = <EditorLine>[];
  var inBlock = false;
  for (final r in rows) {
    if (r.trim().isEmpty) {
      inBlock = false;
      continue;
    }
    final l = lineFromText(r, titleHint: titleHint);
    if (l.isBlock) {
      inBlock = true;
    } else {
      l.inBlock = inBlock;
    }
    out.add(l);
  }
  return out;
}

/// Righe strutturate come le vede l'atleta, con il valore personale calcolato.
class StructuredLines extends StatelessWidget {
  final List<EditorLine> lines;
  final int? maxLines;
  const StructuredLines(this.lines, {super.key, this.maxLines});
  @override
  Widget build(BuildContext context) {
    final shown = lines.where((l) => l.render().trim().isNotEmpty).toList();
    final list = maxLines == null ? shown : shown.take(maxLines!).toList();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      for (final l in list)
        Padding(
          padding: EdgeInsets.only(left: l.inBlock ? 14 : 0, bottom: 4),
          child: l.isBlock
              ? Text(l.render(), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14))
              : Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  if (l.inBlock) Container(width: 2, height: 18, margin: const EdgeInsets.only(right: 10, top: 2), color: Ink.line),
                  Expanded(child: Text(l.render(), style: const TextStyle(fontSize: 14, color: Color(0xFFD6D6D6)))),
                  if (DemoData.computed(l) != null) ...[
                    const SizedBox(width: 8),
                    ComputedChip(l),
                  ],
                ]),
        ),
      if (maxLines != null && shown.length > list.length) const Text('…', style: TextStyle(color: Ink.muted)),
    ]);
  }
}

class ComputedChip extends StatelessWidget {
  final EditorLine l;
  const ComputedChip(this.l, {super.key});
  @override
  Widget build(BuildContext context) {
    final v = DemoData.computed(l)!;
    final missing = v == DemoData.missing;
    final zone = l.loadKind == 'zone' ? (int.tryParse(l.loadValue) ?? 1) : null;
    final c = zone != null ? Ink.zones[zone - 1] : Ink.white;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(border: Border.all(color: missing ? Ink.line : c), borderRadius: BorderRadius.circular(6)),
      child: Text(v, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: missing ? Ink.muted : c, fontStyle: missing ? FontStyle.italic : FontStyle.normal, fontFeatures: const [FontFeature.tabularFigures()])),
    );
  }
}

class WorkoutEditorScreen extends StatefulWidget {
  final DateTime date;
  final Workout? existing;
  final List<EditorLine>? initialLines;
  final String? initialTitle;
  const WorkoutEditorScreen({super.key, required this.date, this.existing, this.initialLines, this.initialTitle});
  @override
  State<WorkoutEditorScreen> createState() => _WorkoutEditorScreenState();
}

class _WorkoutEditorScreenState extends State<WorkoutEditorScreen> {
  late TextEditingController title;
  late DateTime date;
  String category = 'Metcon';
  String format = 'AMRAP';
  String resultType = 'Round + reps';
  int minutes = 12;
  int sets = 5;
  int reps = 5;
  int interval = 60;
  int rounds = 10;
  int cap = 20;
  String audience = session.isStaff ? 'all' : 'personal';
  bool benchmark = false;
  final Set<String> assigned = {};
  final Set<int> weekdays = {};
  late List<EditorLine> lines;

  @override
  void initState() {
    super.initState();
    date = widget.date;
    title = TextEditingController(text: widget.initialTitle ?? widget.existing?.name ?? '');
    lines = widget.initialLines ?? [];
    final ex = widget.existing;
    if (ex != null && lines.isEmpty) {
      lines = ex.lines != null ? [...ex.lines!] : linesFromText(ex.description.split('\n'), titleHint: ex.name);
      final f = ex.format;
      format = switch (f) { 'EMOM' => 'EMOM', 'AMRAP' => 'AMRAP', 'FOR TIME' => 'For time', 'EVERY' => 'Every X min', 'FORZA' => 'Sets × reps', _ => 'Libero' };
      category = f == 'FORZA' ? 'Forza' : (f == 'CONDITIONING' ? 'Monostrutturale' : 'Metcon');
      resultType = switch (format) { 'AMRAP' || 'EMOM' => 'Round + reps', 'For time' => 'Tempo', 'Sets × reps' => 'Carico', _ => 'Nessuno' };
      audience = ex.audience;
    }
    if (lines.isEmpty) lines.add(EditorLine());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.existing == null ? 'NUOVO ALLENAMENTO' : 'MODIFICA'),
        actions: [TextButton(onPressed: () => _save(publish: false), child: const Text('SALVA BOZZA'))],
      ),
      body: ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 120), children: [
        OutlinedButton.icon(
          onPressed: () async {
            final d = await showDatePicker(context: context, initialDate: date, firstDate: DateTime(2025), lastDate: DateTime(2027));
            if (d != null) setState(() => date = d);
          },
          icon: const Icon(Icons.calendar_today_outlined, size: 18),
          label: Text(fmtDateLong(date)),
        ),
        const SizedBox(height: 12),
        TextField(controller: title, decoration: const InputDecoration(labelText: 'Titolo (es. Emom 9\', Back Squat, Fran)')),
        const SizedBox(height: 20),
        const Kicker('Categoria'),
        const SizedBox(height: 8),
        _chips(categories, category, (v) => setState(() => category = v)),
        const SizedBox(height: 16),
        const Kicker('Formato'),
        const SizedBox(height: 8),
        _chips(formats, format, (v) => setState(() {
              format = v;
              resultType = switch (v) { 'AMRAP' || 'EMOM' || 'Every X min' => 'Round + reps', 'For time' => 'Tempo', 'Sets × reps' => 'Carico', 'Tabata' => 'Ripetizioni', _ => 'Nessuno' };
            })),
        const SizedBox(height: 10),
        _formatParams(),
        const SizedBox(height: 16),
        const Kicker('Tipo di risultato'),
        const SizedBox(height: 8),
        _chips(resultTypes, resultType, (v) => setState(() => resultType = v)),
        const SizedBox(height: 24),
        const Kicker('Righe'),
        const SizedBox(height: 4),
        Row(children: [
          Expanded(child: OutlinedButton.icon(style: _small, onPressed: _addExerciseLine, icon: const Icon(Icons.add, size: 16), label: const Text('ESERCIZIO'))),
          const SizedBox(width: 6),
          Expanded(child: OutlinedButton.icon(style: _small, onPressed: () => setState(() => lines.add(EditorLine(kind: 'block', setsMin: 3, setsMax: 3))), icon: const Icon(Icons.repeat, size: 16), label: const Text('BLOCCO'))),
          const SizedBox(width: 6),
          Expanded(child: OutlinedButton.icon(style: _small, onPressed: () => setState(() => lines.add(EditorLine())), icon: const Icon(Icons.notes, size: 16), label: const Text('TESTO'))),
        ]),
        const SizedBox(height: 10),
        ReorderableListView(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          buildDefaultDragHandles: false,
          onReorder: (a, b) => setState(() {
            if (b > a) b--;
            final l = lines.removeAt(a);
            lines.insert(b, l);
          }),
          children: [
            for (var i = 0; i < lines.length; i++)
              _LineCard(
                key: ValueKey(lines[i]),
                index: i,
                line: lines[i],
                onChanged: () => setState(() {}),
                onDelete: () => setState(() => lines.removeAt(i)),
                onPickExercise: () => _pickExercise(lines[i]),
              ),
          ],
        ),
        const SizedBox(height: 24),
        const Kicker('Destinatari'),
        const SizedBox(height: 8),
        if (!session.isStaff) const Text('Allenamento personale: visibile solo a te e al tuo coach.', style: TextStyle(color: Ink.muted, fontSize: 13)),
        if (session.isStaff) _chips(const ['Tutti', 'Atleti scelti'], audience == 'all' ? 'Tutti' : 'Atleti scelti', (v) => setState(() => audience = v == 'Tutti' ? 'all' : 'assigned')),
        if (audience == 'assigned') ...[
          const SizedBox(height: 10),
          Wrap(spacing: 6, runSpacing: 6, children: [
            for (final a in DemoData.athletes.where((a) => a.enabled))
              FilterChip(
                label: Text(a.name),
                selected: assigned.contains(a.username),
                selectedColor: Ink.white,
                checkmarkColor: Ink.black,
                labelStyle: TextStyle(color: assigned.contains(a.username) ? Ink.black : Ink.white),
                onSelected: (s) => setState(() => s ? assigned.add(a.username) : assigned.remove(a.username)),
              ),
          ]),
        ],
        if (audience != 'all') ...[
          const SizedBox(height: 12),
          const Kicker('Ricorrenza settimanale (facoltativa)'),
          const SizedBox(height: 8),
          Row(children: [
            for (var i = 0; i < 7; i++)
              Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => weekdays.contains(i) ? weekdays.remove(i) : weekdays.add(i)),
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(color: weekdays.contains(i) ? Ink.white : Colors.transparent, border: Border.all(color: weekdays.contains(i) ? Ink.white : Ink.line), borderRadius: BorderRadius.circular(6)),
                    child: Center(child: Text(weekdaysShort[i], style: TextStyle(fontWeight: FontWeight.w800, color: weekdays.contains(i) ? Ink.black : Ink.white))),
                  ),
                ),
              ),
          ]),
        ],
        const SizedBox(height: 16),
        SwitchListTile(contentPadding: EdgeInsets.zero, value: benchmark, onChanged: (v) => setState(() => benchmark = v), title: const Text('Benchmark ripetibile'), subtitle: const Text('Confrontabile nel tempo (es. Fran, Grace)', style: TextStyle(color: Ink.muted, fontSize: 12))),
        const SizedBox(height: 20),
        const Kicker('Anteprima per l\'atleta'),
        const SizedBox(height: 8),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title.text.isEmpty ? _defaultTitle() : title.text, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              StructuredLines(lines),
            ]),
          ),
        ),
      ]),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
          child: Row(children: [
            Expanded(child: OutlinedButton(onPressed: () => _save(publish: false), child: const Text('BOZZA'))),
            const SizedBox(width: 10),
            Expanded(flex: 2, child: FilledButton.icon(onPressed: () => _save(publish: true), icon: Icon(session.isStaff ? Icons.publish_outlined : Icons.check), label: Text(session.isStaff ? 'PUBBLICA' : 'SALVA'))),
          ]),
        ),
      ),
    );
  }

  ButtonStyle get _small => OutlinedButton.styleFrom(minimumSize: const Size(0, 40), padding: const EdgeInsets.symmetric(horizontal: 6), textStyle: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, letterSpacing: 0.8));

  Widget _chips(List<String> items, String selected, ValueChanged<String> onSel) => Wrap(spacing: 6, runSpacing: 6, children: [
        for (final it in items)
          ChoiceChip(
            label: Text(it),
            selected: selected == it,
            selectedColor: Ink.white,
            showCheckmark: false,
            labelStyle: TextStyle(color: selected == it ? Ink.black : Ink.white, fontWeight: FontWeight.w700, fontSize: 12),
            onSelected: (_) => onSel(it),
          ),
      ]);

  Widget _formatParams() {
    Widget st(String l, int v, ValueChanged<int> f, {int step = 1}) => Row(children: [
          Expanded(child: Text(l, style: const TextStyle(color: Ink.muted))),
          IconButton.outlined(visualDensity: VisualDensity.compact, onPressed: () => f(v - step), icon: const Icon(Icons.remove, size: 18)),
          SizedBox(width: 48, child: Text('$v', textAlign: TextAlign.center, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800))),
          IconButton.outlined(visualDensity: VisualDensity.compact, onPressed: () => f(v + step), icon: const Icon(Icons.add, size: 18)),
        ]);
    return switch (format) {
      'AMRAP' => st('Durata (min)', minutes, (v) => setState(() => minutes = v.clamp(1, 90))),
      'For time' => st('Time cap (min)', cap, (v) => setState(() => cap = v.clamp(1, 90))),
      'EMOM' => st('Minuti', rounds, (v) => setState(() => rounds = v.clamp(1, 60))),
      'Every X min' => Column(children: [
          st('Ogni (sec)', interval, (v) => setState(() => interval = v.clamp(30, 600)), step: 30),
          st('Set', sets, (v) => setState(() => sets = v.clamp(1, 20))),
        ]),
      'Sets × reps' => Column(children: [
          st('Set', sets, (v) => setState(() => sets = v.clamp(1, 20))),
          st('Ripetizioni', reps, (v) => setState(() => reps = v.clamp(1, 50))),
        ]),
      _ => const SizedBox(),
    };
  }

  String _defaultTitle() => switch (format) {
        'AMRAP' => 'AMRAP $minutes\'',
        'For time' => 'For Time (cap $cap\')',
        'EMOM' => 'Emom $rounds\'',
        'Every X min' => 'Ev. ${interval ~/ 60}\' x $sets sets',
        'Sets × reps' => '$sets x $reps',
        _ => 'Allenamento',
      };

  Future<void> _addExerciseLine() async {
    final l = EditorLine();
    final ok = await _pickExercise(l);
    if (ok) {
      // se l'ultima riga è un blocco o dentro un blocco, la nuova riga ci entra
      if (lines.isNotEmpty && (lines.last.isBlock || lines.last.inBlock)) l.inBlock = true;
      setState(() => lines.add(l));
    }
  }

  Future<bool> _pickExercise(EditorLine l) async {
    final ex = await showModalBottomSheet<CatalogExercise>(context: context, isScrollControlled: true, builder: (_) => const _ExercisePicker());
    if (ex == null) return false;
    setState(() {
      l.exercise = ex;
      l.kind = 'exercise';
      l.freeText = '';
      if (ex.category == 'weightlifting' && l.loadKind == 'none') l.loadKind = 'pct';
      if (ex.category == 'monostructural' && ex.unit != 'reps') {
        l.qtyUnit = 'min';
        if (l.loadKind == 'none') l.loadKind = 'zone';
        if (l.loadValue.isEmpty) l.loadValue = '2';
      }
    });
    return true;
  }

  void _save({required bool publish}) {
    final clean = lines.where((l) => l.render().trim().isNotEmpty).toList();
    final ranges = <String, List<int>>{};
    for (final l in clean) {
      if (l.exercise != null && l.exercise!.category == 'weightlifting' && l.loadKind == 'pct' && int.tryParse(l.loadValue) != null) {
        ranges.putIfAbsent(l.exercise!.name, () => []).add(int.parse(l.loadValue));
      }
    }
    Workout build(int id, DateTime d) => Workout(
          id: id,
          date: d,
          order: widget.existing?.order ?? 50,
          name: title.text.isEmpty ? _defaultTitle() : title.text,
          description: clean.map((l) => '${l.inBlock ? '  ' : ''}${l.render()}').join('\n'),
          ranges: [for (final e in ranges.entries) RangeGroup(e.key, e.value)],
          audience: audience,
          lines: clean,
        );
    final w = build(widget.existing?.id ?? DemoData.nextId(), date);
    if (widget.existing != null) DemoData.workouts.removeWhere((x) => x.id == widget.existing!.id);
    DemoData.workouts.add(w);
    if (audience != 'all' && weekdays.isNotEmpty) {
      for (var k = 1; k <= 28; k++) {
        final d = date.add(Duration(days: k));
        if (weekdays.contains(d.weekday - 1)) DemoData.workouts.add(build(DemoData.nextId(), d));
      }
    }
    DemoData.log.insert(0, LogEntry(DateTime.now(), session.username, session.role.label.toLowerCase(), publish ? 'workout_published' : 'workout_created', '${w.name} · ${fmtDateShort(date)}'));
    Navigator.pop(context, w);
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(!session.isStaff ? 'Allenamento personale salvato.' : (publish ? 'Pubblicato. Notifica inviata agli atleti.' : 'Salvato come bozza.'))));
  }
}

class _LineCard extends StatelessWidget {
  final int index;
  final EditorLine line;
  final VoidCallback onChanged, onDelete, onPickExercise;
  const _LineCard({super.key, required this.index, required this.line, required this.onChanged, required this.onDelete, required this.onPickExercise});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(left: line.inBlock ? 18 : 0, bottom: 6),
      child: Card(
        color: line.isBlock ? Ink.surface2 : Ink.surface1,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(4, 8, 4, 10),
          child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            ReorderableDragStartListener(index: index, child: const Padding(padding: EdgeInsets.fromLTRB(6, 10, 6, 0), child: Icon(Icons.drag_indicator, color: Ink.muted))),
            Expanded(child: line.isBlock ? _block() : (line.isFree ? _free() : _exercise())),
            Column(children: [
              IconButton(visualDensity: VisualDensity.compact, onPressed: onDelete, icon: const Icon(Icons.close, size: 18, color: Ink.muted)),
              if (!line.isBlock)
                IconButton(
                  visualDensity: VisualDensity.compact,
                  tooltip: line.inBlock ? 'Togli dal blocco' : 'Metti nel blocco',
                  onPressed: () {
                    line.inBlock = !line.inBlock;
                    onChanged();
                  },
                  icon: Icon(line.inBlock ? Icons.format_indent_decrease : Icons.format_indent_increase, size: 18, color: line.inBlock ? Ink.white : Ink.muted),
                ),
            ]),
          ]),
        ),
      ),
    );
  }

  Widget _block() {
    Widget st(String label, int v, ValueChanged<int> f) => Row(mainAxisSize: MainAxisSize.min, children: [
          Text(label, style: const TextStyle(color: Ink.muted, fontSize: 12)),
          IconButton(visualDensity: VisualDensity.compact, onPressed: () => f(v - 1), icon: const Icon(Icons.remove, size: 16)),
          Text('$v', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          IconButton(visualDensity: VisualDensity.compact, onPressed: () => f(v + 1), icon: const Icon(Icons.add, size: 16)),
        ]);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Padding(padding: EdgeInsets.only(top: 6), child: Row(children: [Icon(Icons.repeat, size: 16), SizedBox(width: 6), Text('BLOCCO RIPETUTO', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1, fontSize: 12))])),
      Wrap(children: [
        st('da', line.setsMin, (v) {
          line.setsMin = v.clamp(1, 30);
          if (line.setsMax < line.setsMin) line.setsMax = line.setsMin;
          onChanged();
        }),
        st('a', line.setsMax, (v) {
          line.setsMax = v.clamp(line.setsMin, 30);
          onChanged();
        }),
        const Padding(padding: EdgeInsets.only(top: 12, left: 4), child: Text('giri', style: TextStyle(color: Ink.muted, fontSize: 12))),
      ]),
      const Text('Le righe rientrate qui sotto fanno parte del blocco.', style: TextStyle(color: Ink.muted, fontSize: 11)),
    ]);
  }

  Widget _free() => TextFormField(
        initialValue: line.freeText,
        maxLines: null,
        decoration: const InputDecoration(labelText: 'Testo libero (note, scaling, istruzioni)'),
        onChanged: (v) {
          line.freeText = v;
          onChanged();
        },
      );

  Widget _exercise() {
    final ex = line.exercise!;
    final mono = ex.category == 'monostructural';
    final paced = ex.unit == 'pace' || ex.unit == 'min';
    final computed = DemoData.computed(line);
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      InkWell(
        onTap: onPickExercise,
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 6),
          child: Row(children: [
            Expanded(child: Text(ex.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800))),
            Tag(ex.categoryLabel),
            const Icon(Icons.unfold_more, size: 18, color: Ink.muted),
          ]),
        ),
      ),
      const SizedBox(height: 6),
      const Text('QUANTITÀ', style: TextStyle(fontSize: 10, letterSpacing: 1, color: Ink.muted, fontWeight: FontWeight.w700)),
      const SizedBox(height: 4),
      Row(children: [
        SizedBox(width: 80, child: _field(line.qty, 'N°', (v) => line.qty = v)),
        const SizedBox(width: 8),
        Expanded(child: _mini(['reps', 'min', 'sec', 'm', 'cal'], line.qtyUnit, (v) => line.qtyUnit = v)),
      ]),
      const SizedBox(height: 10),
      const Text('INTENSITÀ', style: TextStyle(fontSize: 10, letterSpacing: 1, color: Ink.muted, fontWeight: FontWeight.w700)),
      const SizedBox(height: 4),
      _mini(['none', 'kg', 'pct', 'offset', 'zone'], line.loadKind, (v) {
        line.loadKind = v;
        if (v == 'zone' && (int.tryParse(line.loadValue) ?? 9) > 5) line.loadValue = '2';
        if ((v == 'pct' || v == 'offset') && paced && line.refTest.isEmpty) line.refTest = DemoData.testsFor(ex.name).first;
      }, labels: const {'none': '—', 'kg': 'kg', 'pct': '% test', 'offset': '+sec', 'zone': 'zona FC'}),
      if (line.loadKind == 'zone') ...[
        const SizedBox(height: 8),
        Row(children: [
          for (var z = 1; z <= 5; z++)
            Expanded(
              child: GestureDetector(
                onTap: () {
                  line.loadValue = '$z';
                  onChanged();
                },
                child: Container(
                  margin: const EdgeInsets.only(right: 4),
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  decoration: BoxDecoration(color: line.loadValue == '$z' ? Ink.zones[z - 1] : Colors.transparent, border: Border.all(color: Ink.zones[z - 1]), borderRadius: BorderRadius.circular(6)),
                  child: Center(child: Text('Z$z', style: TextStyle(fontWeight: FontWeight.w800, color: line.loadValue == '$z' ? Ink.black : Ink.zones[z - 1]))),
                ),
              ),
            ),
        ]),
      ],
      if (line.loadKind == 'kg' || line.loadKind == 'pct' || line.loadKind == 'offset') ...[
        const SizedBox(height: 8),
        Row(children: [
          SizedBox(width: 100, child: _field(line.loadValue, switch (line.loadKind) { 'kg' => 'kg', 'pct' => '%', _ => 'secondi' }, (v) => line.loadValue = v)),
          if (line.loadKind != 'kg' && paced) ...[
            const SizedBox(width: 8),
            const Text('del test', style: TextStyle(color: Ink.muted, fontSize: 12)),
            const SizedBox(width: 6),
            Expanded(child: SingleChildScrollView(scrollDirection: Axis.horizontal, child: _mini(DemoData.testsFor(ex.name), line.refTest, (v) => line.refTest = v))),
          ],
          if (line.loadKind == 'pct' && !paced) const Padding(padding: EdgeInsets.only(left: 8), child: Text('del massimale', style: TextStyle(color: Ink.muted, fontSize: 12))),
        ]),
      ],
      if (mono) ...[
        const SizedBox(height: 8),
        SizedBox(width: 190, child: _field(line.cadence, 'Ritmo s/m (es. 20-22)', (v) => line.cadence = v, numeric: false)),
      ],
      const SizedBox(height: 8),
      _field(line.note, 'Nota (tempo, pausa, scaling)', (v) => line.note = v, numeric: false),
      if (computed != null) ...[
        const SizedBox(height: 8),
        Row(children: [
          const Icon(Icons.person_outline, size: 14, color: Ink.muted),
          const SizedBox(width: 4),
          const Text('Per l\'atleta demo: ', style: TextStyle(fontSize: 12, color: Ink.muted)),
          Text(computed, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
        ]),
      ],
    ]);
  }

  Widget _field(String initial, String label, ValueChanged<String> set, {bool numeric = true}) => TextFormField(
        initialValue: initial,
        keyboardType: numeric ? TextInputType.number : TextInputType.text,
        decoration: InputDecoration(labelText: label, isDense: true),
        onChanged: (v) {
          set(v);
          onChanged();
        },
      );

  Widget _mini(List<String> vals, String sel, ValueChanged<String> f, {Map<String, String>? labels}) => Align(
        alignment: Alignment.centerLeft,
        child: Container(
          decoration: BoxDecoration(border: Border.all(color: Ink.line), borderRadius: BorderRadius.circular(6)),
          clipBehavior: Clip.antiAlias,
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            for (final v in vals)
              GestureDetector(
                onTap: () {
                  f(v);
                  onChanged();
                },
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  color: sel == v ? Ink.white : Colors.transparent,
                  child: Text(labels?[v] ?? v, style: TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: sel == v ? Ink.black : Ink.white)),
                ),
              ),
          ]),
        ),
      );
}

class _ExercisePicker extends StatefulWidget {
  const _ExercisePicker();
  @override
  State<_ExercisePicker> createState() => _ExercisePickerState();
}

class _ExercisePickerState extends State<_ExercisePicker> {
  String q = '';
  String cat = 'Tutti';
  @override
  Widget build(BuildContext context) {
    final ql = q.toLowerCase();
    final list = DemoData.catalog.where((e) {
      if (cat != 'Tutti' && e.categoryLabel != cat) return false;
      if (ql.isEmpty) return true;
      return e.name.toLowerCase().contains(ql) || e.aliases.any((a) => a.contains(ql));
    }).toList();
    return SizedBox(
      height: MediaQuery.of(context).size.height * 0.85,
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: TextField(autofocus: true, decoration: const InputDecoration(labelText: 'Cerca esercizio (anche alias: c2b, t2b, hspu…)', prefixIcon: Icon(Icons.search)), onChanged: (v) => setState(() => q = v)),
        ),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(children: [
            for (final c in ['Tutti', 'Pesistica', 'Monostrutturale', 'Corpo libero', 'Skill']) ...[
              ChoiceChip(
                label: Text(c, style: const TextStyle(fontSize: 11)),
                selected: cat == c,
                selectedColor: Ink.white,
                showCheckmark: false,
                labelStyle: TextStyle(color: cat == c ? Ink.black : Ink.white, fontWeight: FontWeight.w700),
                onSelected: (_) => setState(() => cat = c),
              ),
              const SizedBox(width: 4),
            ],
          ]),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: ListView.separated(
            itemCount: list.length + (q.isNotEmpty ? 1 : 0),
            separatorBuilder: (_, _) => const Divider(),
            itemBuilder: (context, i) {
              if (i == list.length) {
                return ListTile(
                  leading: const Icon(Icons.add_circle_outline),
                  title: Text('Crea "$q" nel catalogo'),
                  subtitle: const Text('Categoria e unità da confermare', style: TextStyle(color: Ink.muted, fontSize: 12)),
                  onTap: () {
                    final e = CatalogExercise(q, 'bodyweight', 'reps', []);
                    DemoData.catalog.add(e);
                    Navigator.pop(context, e);
                  },
                );
              }
              final e = list[i];
              final tests = DemoData.maxRecords.where((m) => m.exercise == e.name).map((m) => m.test.isEmpty ? m.testType : m.test).toSet();
              return ListTile(
                title: Text(e.name, style: const TextStyle(fontWeight: FontWeight.w700)),
                subtitle: Text('${e.categoryLabel} · ${e.unit}${e.aliases.isNotEmpty ? ' · ${e.aliases.take(3).join(', ')}' : ''}', style: const TextStyle(color: Ink.muted, fontSize: 12), maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: tests.isNotEmpty ? Text('test: ${tests.join(', ')}', style: const TextStyle(color: Ink.muted, fontSize: 11)) : null,
                onTap: () => Navigator.pop(context, e),
              );
            },
          ),
        ),
      ]),
    );
  }
}

/// Inserimento esercizi da testo (formato del coach) con anteprima strutturata.
class ImportTextScreen extends StatefulWidget {
  final DateTime monday;
  const ImportTextScreen({super.key, required this.monday});
  @override
  State<ImportTextScreen> createState() => _ImportTextScreenState();
}

class _ImportTextScreenState extends State<ImportTextScreen> {
  late final TextEditingController text;
  List<_ParsedWorkout>? parsed;

  @override
  void initState() {
    super.initState();
    text = TextEditingController(text: '''lunedì
work 1: Squat Snatch
5 x 2 73%
Rest 1'30"
work 2: Emom 9'
A) 12/10 Cal Row
B) 10 Toes To Bar
C) 6 Bar Muscle Up

martedì
work 1: Monostructural
5’ Row Z2
3 To 4 Sets
4’ Row 95% (or 5” +) From Test 2K (20-22 s/m)
1’ Row Active Rest 85% ( or 10” -15” +) From Test 2K
work 2: For Time
21-15-9
Thruster 43/30
Pull Up
Cap 10'
''');
  }

  void _parse() {
    const days = {
      'lunedì': 0, 'martedì': 1, 'mercoledì': 2, 'giovedì': 3, 'venerdì': 4, 'sabato': 5, 'domenica': 6,
      'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6,
    };
    final out = <_ParsedWorkout>[];
    var day = 0;
    _ParsedWorkout? cur;
    for (final raw in text.text.split('\n')) {
      final l = raw.trim();
      if (l.isEmpty) continue;
      final dl = l.toLowerCase().replaceFirst(RegExp(r'^day\s*:\s*'), '').replaceAll(':', '').trim();
      if (days.containsKey(dl)) {
        day = days[dl]!;
        cur = null;
        continue;
      }
      final m = RegExp(r'^work\s*\d+\s*:\s*(.*)$', caseSensitive: false).firstMatch(l);
      if (m != null) {
        cur = _ParsedWorkout(day, m.group(1)!.trim().isEmpty ? 'Allenamento' : m.group(1)!.trim());
        out.add(cur);
        continue;
      }
      if (cur == null) {
        cur = _ParsedWorkout(day, 'Allenamento');
        out.add(cur);
      }
      cur.raw.add(l);
    }
    for (final p in out) {
      p.lines = linesFromText(p.raw, titleHint: p.title);
    }
    setState(() => parsed = out);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ESERCIZI DA TESTO')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const Text('Incolla il programma come lo scrivi di solito: il giorno, poi "work N: titolo" per ogni blocco. Il sistema lo interpreta e ti mostra l\'anteprima da correggere prima di salvare.', style: TextStyle(color: Ink.muted, fontSize: 13)),
        const SizedBox(height: 12),
        TextField(controller: text, maxLines: 12, style: const TextStyle(fontFamily: 'monospace', fontSize: 13), decoration: const InputDecoration(labelText: 'Testo del programma')),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: _parse, icon: const Icon(Icons.auto_awesome), label: const Text('ANALIZZA')),
        if (parsed != null) ...[
          const SizedBox(height: 24),
          Row(children: [
            const Expanded(child: Kicker('Anteprima strutturata')),
            Text('${parsed!.length} allenamenti', style: const TextStyle(color: Ink.muted, fontSize: 12)),
          ]),
          const SizedBox(height: 8),
          for (final p in parsed!) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Tag(weekdaysLong[p.day]),
                    const SizedBox(width: 8),
                    Expanded(child: Text(p.title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16))),
                    IconButton(
                      visualDensity: VisualDensity.compact,
                      onPressed: () async {
                        await Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: widget.monday.add(Duration(days: p.day)), initialTitle: p.title, initialLines: p.lines)));
                        if (mounted) setState(() {});
                      },
                      icon: const Icon(Icons.edit_outlined, size: 18),
                    ),
                  ]),
                  const SizedBox(height: 8),
                  for (var i = 0; i < p.lines.length; i++)
                    Padding(
                      padding: EdgeInsets.only(bottom: 6, left: p.lines[i].inBlock ? 14 : 0),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Icon(p.lines[i].isBlock ? Icons.repeat : (p.lines[i].isFree ? Icons.notes : Icons.check_circle_outline), size: 16, color: p.lines[i].isFree ? Ink.muted : Ink.white),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            Text(p.lines[i].render(), style: TextStyle(color: p.lines[i].isFree ? Ink.muted : Ink.white, fontWeight: p.lines[i].isBlock ? FontWeight.w800 : FontWeight.w400)),
                            if (!p.lines[i].isFree && !p.lines[i].isBlock && i < p.raw.length) Text('da: ${p.raw[i]}', style: const TextStyle(fontSize: 11, color: Ink.muted), maxLines: 1, overflow: TextOverflow.ellipsis),
                          ]),
                        ),
                        if (DemoData.computed(p.lines[i]) != null) ComputedChip(p.lines[i]),
                      ]),
                    ),
                ]),
              ),
            ),
            const SizedBox(height: 10),
          ],
          const SizedBox(height: 8),
          const Text('Spunta: riga agganciata a un esercizio del catalogo, con il valore calcolato per l\'atleta demo. Frecce circolari: blocco ripetuto. Le altre restano testo libero. Tocca la matita per correggere.', style: TextStyle(color: Ink.muted, fontSize: 12)),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () {
              for (final p in parsed!) {
                final ranges = <String, List<int>>{};
                for (final l in p.lines) {
                  if (l.exercise != null && l.exercise!.category == 'weightlifting' && l.loadKind == 'pct' && int.tryParse(l.loadValue) != null) {
                    ranges.putIfAbsent(l.exercise!.name, () => []).add(int.parse(l.loadValue));
                  }
                }
                DemoData.workouts.add(Workout(
                  id: DemoData.nextId(),
                  date: widget.monday.add(Duration(days: p.day)),
                  order: 50,
                  name: p.title,
                  description: p.raw.join('\n'),
                  ranges: [for (final e in ranges.entries) RangeGroup(e.key, e.value)],
                  lines: p.lines,
                ));
              }
              DemoData.log.insert(0, LogEntry(DateTime.now(), session.username, session.role.label.toLowerCase(), 'weekly_import', '${parsed!.length} allenamenti in bozza'));
              final n = parsed!.length;
              Navigator.pop(context, true);
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$n allenamenti salvati in bozza.')));
            },
            child: const Text('SALVA TUTTO IN BOZZA'),
          ),
        ],
      ]),
    );
  }
}

class _ParsedWorkout {
  final int day;
  final String title;
  final List<String> raw = [];
  List<EditorLine> lines = [];
  _ParsedWorkout(this.day, this.title);
}
