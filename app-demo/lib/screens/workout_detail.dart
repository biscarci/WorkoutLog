import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';
import '../main.dart';
import 'today.dart';
import 'timer.dart';
import 'cardio.dart';
import 'editor.dart';

class WorkoutDetailScreen extends StatefulWidget {
  final Workout w;
  const WorkoutDetailScreen(this.w, {super.key});
  @override
  State<WorkoutDetailScreen> createState() => _WorkoutDetailScreenState();
}

class _WorkoutDetailScreenState extends State<WorkoutDetailScreen> {
  String? myScore;
  bool rx = true;

  @override
  Widget build(BuildContext context) {
    final w = widget.w;
    final canLeaderboard = w.audience == 'all';
    return DefaultTabController(
      length: canLeaderboard ? 2 : 1,
      child: Scaffold(
        appBar: AppBar(
          title: Text(fmtDateLong(w.date).toUpperCase(), style: const TextStyle(fontSize: 14, letterSpacing: 1.5)),
          actions: [
            if (session.isStaff) IconButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: w.date, existing: w))), icon: const Icon(Icons.edit_outlined)),
          ],
        ),
        body: Column(children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
              children: [
                Row(children: [
                  Tag(w.format, filled: true),
                  const SizedBox(width: 6),
                  if (w.audience == 'assigned') const Tag('Dedicato'),
                  if (w.audience == 'personal') const Tag('Personale'),
                ]),
                const SizedBox(height: 10),
                Text(w.name, style: Theme.of(context).textTheme.headlineMedium),
                const SizedBox(height: 14),
                if (w.lines != null) StructuredLines(w.lines!) else SelectableText(w.description, style: const TextStyle(fontSize: 15, height: 1.5)),
                if (w.ranges.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Kicker('I tuoi carichi'),
                  const SizedBox(height: 8),
                  for (final g in w.ranges) PercentRow(g),
                ],
                const SizedBox(height: 20),
                if (session.hrBand) const CardioPanel(compact: false),
                const SizedBox(height: 20),
                FilledButton.icon(
                  onPressed: () async {
                    final res = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => TimerSetupScreen(w)));
                    if (res != null) setState(() => myScore = res);
                  },
                  icon: const Icon(Icons.timer_outlined),
                  label: const Text('AVVIA TIMER'),
                ),
                const SizedBox(height: 24),
                TabBar(tabs: [const Tab(text: 'IL MIO SCORE'), if (canLeaderboard) const Tab(text: 'CLASSIFICA')]),
                SizedBox(
                  height: 420,
                  child: TabBarView(children: [
                    _MyScore(w: w, score: myScore, rx: rx, onRx: (v) => setState(() => rx = v), onSave: (s) => setState(() => myScore = s)),
                    if (canLeaderboard) _Leaderboard(w, myScore, rx),
                  ]),
                ),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

class _MyScore extends StatefulWidget {
  final Workout w;
  final String? score;
  final bool rx;
  final ValueChanged<bool> onRx;
  final ValueChanged<String> onSave;
  const _MyScore({required this.w, required this.score, required this.rx, required this.onRx, required this.onSave});
  @override
  State<_MyScore> createState() => _MyScoreState();
}

class _MyScoreState extends State<_MyScore> {
  final a = TextEditingController();
  final b = TextEditingController();
  final notes = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final f = widget.w.format;
    final isTime = f == 'FOR TIME' || f == 'CONDITIONING';
    final isRounds = f == 'AMRAP' || f == 'EMOM';
    final label1 = isTime ? 'Minuti' : (isRounds ? 'Round' : 'Carico (kg)');
    final label2 = isTime ? 'Secondi' : 'Ripetizioni extra';
    return ListView(padding: const EdgeInsets.only(top: 16), children: [
      if (widget.score != null) ...[
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(children: [
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Kicker('Score registrato'),
                  const SizedBox(height: 4),
                  Text(widget.score!, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
                ]),
              ),
              Tag(widget.rx ? 'Rx' : 'Scalato', filled: true),
            ]),
          ),
        ),
        const SizedBox(height: 12),
      ],
      Row(children: [
        Expanded(child: TextField(controller: a, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: label1))),
        if (isTime || isRounds) ...[
          const SizedBox(width: 10),
          Expanded(child: TextField(controller: b, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: label2))),
        ],
      ]),
      const SizedBox(height: 10),
      Row(children: [
        const Text('Rx'),
        Switch(value: widget.rx, onChanged: widget.onRx),
        const Text('Scalato', style: TextStyle(color: Ink.muted)),
      ]),
      TextField(controller: notes, decoration: const InputDecoration(labelText: 'Note (facoltative)')),
      const SizedBox(height: 14),
      OutlinedButton(
        onPressed: () {
          String s;
          if (isTime) {
            s = '${a.text.isEmpty ? '0' : a.text}:${(b.text.isEmpty ? '0' : b.text).padLeft(2, '0')}';
          } else if (isRounds) {
            s = '${a.text.isEmpty ? '0' : a.text} round${b.text.isNotEmpty && b.text != '0' ? ' + ${b.text}' : ''}';
          } else {
            s = '${a.text.isEmpty ? '0' : a.text} kg';
          }
          widget.onSave(s);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Score salvato.')));
        },
        child: Text(widget.score == null ? 'SALVA SCORE' : 'AGGIORNA SCORE'),
      ),
    ]);
  }
}

class _Leaderboard extends StatelessWidget {
  final Workout w;
  final String? mine;
  final bool rx;
  const _Leaderboard(this.w, this.mine, this.rx);
  @override
  Widget build(BuildContext context) {
    final rows = DemoData.leaderboard(w);
    final all = [...rows];
    if (mine != null) all.insert(2, Score(w.id, session.name, mine!, rx: rx));
    return ListView.separated(
      padding: const EdgeInsets.only(top: 8),
      itemCount: all.length,
      separatorBuilder: (_, __) => const Divider(),
      itemBuilder: (context, i) {
        final s = all[i];
        final me = s.athlete == session.name;
        return Container(
          color: me ? Ink.surface2 : Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
          child: Row(children: [
            SizedBox(width: 28, child: Text('${i + 1}', style: const TextStyle(fontWeight: FontWeight.w800, color: Ink.muted))),
            Expanded(child: Text(s.athlete, style: TextStyle(fontWeight: me ? FontWeight.w800 : FontWeight.w500))),
            Text(s.result, style: const TextStyle(fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
            const SizedBox(width: 10),
            Tag(s.rx ? 'Rx' : 'Sc', filled: s.rx),
          ]),
        );
      },
    );
  }
}
