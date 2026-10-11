import 'dart:async';
import 'package:flutter/material.dart' hide Ink;
import 'package:flutter/services.dart';
import 'package:wakelock_plus/wakelock_plus.dart';
import 'package:audioplayers/audioplayers.dart';
import 'editor.dart';
import '../data.dart';
import '../theme.dart';
import '../main.dart';
import 'cardio.dart';

enum TimerKind { amrap, forTime, emom, tabata, forza, cronometro }

extension on TimerKind {
  String get label => switch (this) {
        TimerKind.amrap => 'AMRAP',
        TimerKind.forTime => 'FOR TIME',
        TimerKind.emom => 'EMOM',
        TimerKind.tabata => 'TABATA',
        TimerKind.forza => 'FORZA',
        TimerKind.cronometro => 'TIMER',
      };
}

class TimerSetupScreen extends StatefulWidget {
  final Workout w;
  const TimerSetupScreen(this.w, {super.key});
  @override
  State<TimerSetupScreen> createState() => _TimerSetupScreenState();
}

class _TimerSetupScreenState extends State<TimerSetupScreen> {
  late TimerKind kind;
  int minutes = 12;
  int cap = 20;
  int interval = 60;
  int rounds = 9;

  @override
  void initState() {
    super.initState();
    final f = widget.w.format;
    kind = switch (f) {
      'AMRAP' => TimerKind.amrap,
      'EMOM' => TimerKind.emom,
      'EVERY' => TimerKind.emom,
      'FOR TIME' => TimerKind.forTime,
      'CONDITIONING' => TimerKind.forTime,
      'FORZA' => TimerKind.forza,
      _ => TimerKind.cronometro,
    };
    final m = RegExp(r"(\d+)\s*[’'′]").firstMatch(widget.w.name);
    if (m != null) {
      final v = int.parse(m.group(1)!);
      if (kind == TimerKind.emom) {
        rounds = v;
      } else {
        minutes = v;
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('TIMER')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Text(widget.w.name, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 16),
        Wrap(spacing: 8, runSpacing: 8, children: [
          for (final k in TimerKind.values)
            ChoiceChip(
              label: Text(k.label),
              selected: kind == k,
              selectedColor: Ink.white,
              labelStyle: TextStyle(color: kind == k ? Ink.black : Ink.white, fontWeight: FontWeight.w700),
              onSelected: (_) => setState(() => kind = k),
            ),
        ]),
        const SizedBox(height: 20),
        if (kind == TimerKind.amrap) _Stepper('Durata (min)', minutes, (v) => setState(() => minutes = v.clamp(1, 90))),
        if (kind == TimerKind.forTime) _Stepper('Time cap (min)', cap, (v) => setState(() => cap = v.clamp(1, 90))),
        if (kind == TimerKind.emom) ...[
          _Stepper('Intervallo (sec)', interval, (v) => setState(() => interval = v.clamp(10, 600)), step: 10),
          _Stepper('Round', rounds, (v) => setState(() => rounds = v.clamp(1, 60))),
        ],
        if (kind == TimerKind.tabata) const Text('8 round · 20" lavoro / 10" riposo', style: TextStyle(color: Ink.muted)),
        if (kind == TimerKind.forza) _Stepper('Recupero tra i set (sec)', interval, (v) => setState(() => interval = v.clamp(30, 600)), step: 15),
        const SizedBox(height: 20),
        if (session.hrBand) const CardioPanel(compact: false),
        const SizedBox(height: 24),
        FilledButton(
          onPressed: () async {
            final res = await Navigator.push<String>(
              context,
              MaterialPageRoute(builder: (_) => TimerRunScreen(w: widget.w, kind: kind, minutes: minutes, cap: cap, interval: interval, rounds: rounds)),
            );
            if (!context.mounted) return;
            Navigator.pop(context, res);
          },
          child: const Text('AVVIA'),
        ),
      ]),
    );
  }
}

class _Stepper extends StatelessWidget {
  final String label;
  final int value;
  final int step;
  final ValueChanged<int> onChanged;
  const _Stepper(this.label, this.value, this.onChanged, {this.step = 1});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(children: [
          Expanded(child: Text(label)),
          IconButton.outlined(onPressed: () => onChanged(value - step), icon: const Icon(Icons.remove)),
          SizedBox(width: 64, child: Text('$value', textAlign: TextAlign.center, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800))),
          IconButton.outlined(onPressed: () => onChanged(value + step), icon: const Icon(Icons.add)),
        ]),
      );
}

class TimerRunScreen extends StatefulWidget {
  final Workout w;
  final TimerKind kind;
  final int minutes, cap, interval, rounds;
  const TimerRunScreen({super.key, required this.w, required this.kind, required this.minutes, required this.cap, required this.interval, required this.rounds});
  @override
  State<TimerRunScreen> createState() => _TimerRunScreenState();
}

class _TimerRunScreenState extends State<TimerRunScreen> {
  Timer? t;
  int countdown = 10;
  int elapsed = 0;
  bool running = false;
  bool finished = false;
  int roundsDone = 0;
  int extraReps = 0;
  final _short = AudioPlayer();
  final _long = AudioPlayer();

  Future<void> _beep({bool long = false}) async {
    final p = long ? _long : _short;
    await p.stop();
    await p.play(AssetSource(long ? 'beep_long.wav' : 'beep_short.wav'), mode: PlayerMode.lowLatency);
  }

  int get total => switch (widget.kind) {
        TimerKind.amrap => widget.minutes * 60,
        TimerKind.forTime => widget.cap * 60,
        TimerKind.emom => widget.interval * widget.rounds,
        TimerKind.tabata => 8 * 30,
        _ => 0,
      };

  @override
  void initState() {
    super.initState();
    WakelockPlus.enable();
    t = Timer.periodic(const Duration(seconds: 1), _tick);
  }

  void _tick(Timer _) {
    if (finished) return;
    setState(() {
      if (countdown > 0) {
        countdown--;
        if (countdown <= 3 && countdown > 0) {
          HapticFeedback.mediumImpact();
          _beep();
        }
        if (countdown == 0) {
          running = true;
          HapticFeedback.heavyImpact();
          _beep(long: true);
          HeartRateSim.instance.beginWorkout();
        }
        return;
      }
      if (!running) return;
      elapsed++;
      final left = total > 0 ? total - elapsed : -1;
      if (widget.kind == TimerKind.emom) {
        final inRound = elapsed % widget.interval;
        if (inRound == 0) { HapticFeedback.mediumImpact(); _beep(long: true); }
        else if (widget.interval - inRound <= 3) _beep();
      }
      if (widget.kind == TimerKind.tabata) {
        if (elapsed % 10 == 0) { HapticFeedback.mediumImpact(); _beep(long: true); }
        else if (10 - elapsed % 10 <= 3) _beep();
      }
      if ((widget.kind == TimerKind.amrap || widget.kind == TimerKind.forTime) && left > 0 && left <= 3) _beep();
      if (total > 0 && elapsed >= total) _finish();
    });
  }

  void _finish() {
    finished = true;
    running = false;
    HeartRateSim.instance.endWorkout();
    HapticFeedback.heavyImpact();
    _beep(long: true);
  }

  @override
  void dispose() {
    t?.cancel();
    _short.dispose();
    _long.dispose();
    WakelockPlus.disable();
    HeartRateSim.instance.endWorkout();
    super.dispose();
  }

  String _fmt(int s) => '${(s ~/ 60).toString().padLeft(2, '0')}:${(s % 60).toString().padLeft(2, '0')}';

  String get proposedScore => switch (widget.kind) {
        TimerKind.amrap => '$roundsDone round${extraReps > 0 ? ' + $extraReps' : ''}',
        TimerKind.forTime => _fmt(elapsed),
        TimerKind.emom => '${(elapsed / widget.interval).floor()} round',
        _ => _fmt(elapsed),
      };

  @override
  Widget build(BuildContext context) {
    final k = widget.kind;
    final remaining = total > 0 ? total - elapsed : elapsed;
    String big;
    String sub = '';
    if (countdown > 0) {
      big = '$countdown';
      sub = 'PREPARATI';
    } else if (k == TimerKind.emom) {
      final inRound = elapsed % widget.interval;
      big = _fmt(widget.interval - inRound);
      sub = 'ROUND ${(elapsed ~/ widget.interval) + 1} / ${widget.rounds}';
    } else if (k == TimerKind.tabata) {
      final phase = (elapsed ~/ 10) % 3;
      final r = elapsed ~/ 30 + 1;
      big = '${phase < 2 ? 20 - (elapsed % 30) : 10 - (elapsed % 10)}';
      sub = '${phase < 2 ? 'LAVORO' : 'RIPOSO'} · ROUND $r / 8';
    } else if (k == TimerKind.forza || k == TimerKind.cronometro) {
      big = _fmt(elapsed);
      sub = k == TimerKind.forza ? 'SET ${roundsDone + 1}' : '';
    } else {
      big = _fmt(remaining.clamp(0, 99999));
      sub = k.label;
    }
    if (finished) {
      big = _fmt(elapsed);
      sub = 'FINITO';
    }

    return Scaffold(
      backgroundColor: Ink.black,
      body: SafeArea(
        child: Column(children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: Row(children: [
              IconButton(onPressed: () => _confirmExit(context), icon: const Icon(Icons.close)),
              const Spacer(),
              Text(k.label, style: const TextStyle(letterSpacing: 2, fontWeight: FontWeight.w800, color: Ink.muted)),
              const Spacer(),
              const SizedBox(width: 48),
            ]),
          ),
          if (session.hrBand) const Padding(padding: EdgeInsets.fromLTRB(16, 8, 16, 0), child: CardioPanel(compact: true)),
          GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: running && (k == TimerKind.amrap || k == TimerKind.forza) ? () => setState(() => roundsDone++) : null,
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 18),
              child: Center(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text(sub, style: const TextStyle(letterSpacing: 3, fontWeight: FontWeight.w800, color: Ink.muted)),
                  const SizedBox(height: 8),
                  FittedBox(
                    child: Text(big,
                        style: TextStyle(
                          fontSize: countdown > 0 ? 150 : 104,
                          fontWeight: FontWeight.w800,
                          fontFamily: 'monospace',
                          height: 1,
                          fontFeatures: const [FontFeature.tabularFigures()],
                        )),
                  ),
                  const SizedBox(height: 16),
                  if (running && k == TimerKind.amrap) ...[
                    Text('$roundsDone ROUND', style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 4),
                    const Text('Tocca lo schermo per +1 round', style: TextStyle(color: Ink.muted)),
                  ],
                  if (running && k == TimerKind.forza) const Text('Tocca lo schermo a fine set', style: TextStyle(color: Ink.muted)),
                ]),
              ),
            ),
          ),
          if (!finished)
            Expanded(
              child: Container(
                margin: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(color: Ink.surface1, border: Border.all(color: Ink.line), borderRadius: BorderRadius.circular(8)),
                child: SingleChildScrollView(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(widget.w.name, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    const SizedBox(height: 6),
                    if (widget.w.lines != null) StructuredLines(widget.w.lines!) else Text(widget.w.description, style: const TextStyle(fontSize: 14, color: Color(0xFFD6D6D6), height: 1.4)),
                    if (widget.w.ranges.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      for (final g in widget.w.ranges) _RangeLine(g),
                    ],
                  ]),
                ),
              ),
            ),
          if (finished) _FinishPanel(score: proposedScore, onSave: () => Navigator.pop(context, proposedScore)),
          if (!finished)
            Padding(
              padding: const EdgeInsets.all(16),
              child: Row(children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: countdown > 0 ? null : () => setState(() => running = !running),
                    child: Text(running ? 'PAUSA' : 'RIPRENDI'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(child: FilledButton(onPressed: countdown > 0 ? null : () => setState(_finish), child: const Text('TERMINA'))),
              ]),
            ),
        ]),
      ),
    );
  }

  void _confirmExit(BuildContext context) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Uscire dal timer?'),
        content: const Text('Il tempo verrà fermato e lo score non sarà salvato.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(c, false), child: const Text('ANNULLA')),
          TextButton(onPressed: () => Navigator.pop(c, true), child: const Text('ESCI')),
        ],
      ),
    );
    if (ok == true && context.mounted) Navigator.pop(context);
  }
}

class _FinishPanel extends StatelessWidget {
  final String score;
  final VoidCallback onSave;
  const _FinishPanel({required this.score, required this.onSave});
  @override
  Widget build(BuildContext context) {
    final sim = HeartRateSim.instance;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(color: Ink.surface1, border: Border(top: BorderSide(color: Ink.line))),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Kicker('Score proposto'),
        const SizedBox(height: 4),
        Text(score, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800)),
        if (session.hrBand && sim.samples.isNotEmpty) ...[
          const SizedBox(height: 12),
          Row(children: [
            _Stat('MEDIA', '${sim.avg}'),
            const SizedBox(width: 20),
            _Stat('MAX', '${sim.maxSeen}'),
            const SizedBox(width: 20),
            _Stat('DURATA', '${sim.samples.length ~/ 60}:${(sim.samples.length % 60).toString().padLeft(2, '0')}'),
          ]),
          const SizedBox(height: 10),
          ZoneBars(sim.zoneSeconds),
        ],
        const SizedBox(height: 8),
        Center(child: Text(DemoData.motivational[score.length % DemoData.motivational.length], style: const TextStyle(fontSize: 11, letterSpacing: 2, fontWeight: FontWeight.w800, color: Ink.muted))),
        const SizedBox(height: 12),
        Row(children: [
          Expanded(child: OutlinedButton(onPressed: () => Navigator.pop(context), child: const Text('SCARTA'))),
          const SizedBox(width: 10),
          Expanded(child: FilledButton(onPressed: onSave, child: const Text('SALVA'))),
        ]),
      ]),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label, value;
  const _Stat(this.label, this.value);
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Kicker(label),
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
      ]);
}


class _RangeLine extends StatelessWidget {
  final RangeGroup g;
  const _RangeLine(this.g);
  @override
  Widget build(BuildContext context) {
    final m = DemoData.currentMax(g.exercise);
    if (m == null) return Text('${g.exercise}: massimale non registrato', style: const TextStyle(fontSize: 12, color: Ink.muted));
    return Text('${g.exercise}: ${g.values.map((v) => '$v% ${fmtKg(m.value * v / 100)}').join(' · ')}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700));
  }
}
