import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';
import '../main.dart';
import 'workout_detail.dart';
import 'messages.dart';
import 'editor.dart';

class TodayScreen extends StatefulWidget {
  const TodayScreen({super.key});
  @override
  State<TodayScreen> createState() => _TodayScreenState();
}

class _TodayScreenState extends State<TodayScreen> {
  DateTime selected = DemoData.today;

  DateTime get monday => selected.subtract(Duration(days: selected.weekday - 1));

  @override
  Widget build(BuildContext context) {
    final list = DemoData.forDay(selected);
    final unread = DemoData.messages.where((m) => !m.read).length;
    final pinned = DemoData.messages.where((m) => m.pinned).toList();
    return Scaffold(
      appBar: AppBar(
        title: const Logo(width: 120),
        centerTitle: true,
        leading: const SizedBox(width: 48),
        actions: [
          IconButton(
            tooltip: session.isStaff ? 'Nuovo allenamento' : 'Allenamento personale',
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: selected))).then((_) => setState(() {})),
            icon: const Icon(Icons.add_circle_outline),
          ),
          IconButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MessagesScreen())).then((_) => setState(() {})),
            icon: Badge(isLabelVisible: unread > 0, label: Text('$unread'), backgroundColor: Ink.white, textColor: Ink.black, child: const Icon(Icons.mail_outline)),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 4, 16, 24),
        children: [
          Row(children: [
            IconButton(onPressed: () => setState(() => selected = selected.subtract(const Duration(days: 7))), icon: const Icon(Icons.chevron_left)),
            Expanded(child: Center(child: Text(fmtDateLong(selected), style: Theme.of(context).textTheme.titleLarge))),
            IconButton(onPressed: () => setState(() => selected = selected.add(const Duration(days: 7))), icon: const Icon(Icons.chevron_right)),
          ]),
          const SizedBox(height: 8),
          _WeekStrip(monday: monday, selected: selected, onSelect: (d) => setState(() => selected = d)),
          const SizedBox(height: 20),
          if (!session.enabled) const _WaitingCard(),
          for (final m in pinned) ...[
            _PinnedMessage(m),
            const SizedBox(height: 12),
          ],
          if (list.isEmpty) _EmptyDay(selected, onAdded: () => setState(() {})) else ...[
            for (final w in list) ...[
              _WorkoutCard(w),
              const SizedBox(height: 12),
            ],
            const SizedBox(height: 12),
            Center(
              child: Text(
                DemoData.motivational[selected.day % DemoData.motivational.length],
                style: const TextStyle(fontSize: 12, letterSpacing: 2, fontWeight: FontWeight.w800, color: Ink.muted),
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _WeekStrip extends StatelessWidget {
  final DateTime monday, selected;
  final ValueChanged<DateTime> onSelect;
  const _WeekStrip({required this.monday, required this.selected, required this.onSelect});
  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(7, (i) {
        final d = monday.add(Duration(days: i));
        final sel = d.day == selected.day && d.month == selected.month;
        final isToday = d.day == DemoData.today.day && d.month == DemoData.today.month;
        final has = DemoData.forDay(d).isNotEmpty;
        return Expanded(
          child: GestureDetector(
            onTap: () => onSelect(d),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 3),
              padding: const EdgeInsets.symmetric(vertical: 10),
              decoration: BoxDecoration(
                color: sel ? Ink.white : Colors.transparent,
                border: Border.all(color: sel ? Ink.white : (isToday ? Ink.muted : Ink.line)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(children: [
                Text(weekdaysShort[i], style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: sel ? Ink.black : Ink.muted)),
                const SizedBox(height: 4),
                Text('${d.day}', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w800, color: sel ? Ink.black : Ink.white)),
                const SizedBox(height: 5),
                Container(width: 5, height: 5, decoration: BoxDecoration(shape: BoxShape.circle, color: has ? (sel ? Ink.black : Ink.white) : Colors.transparent)),
              ]),
            ),
          ),
        );
      }),
    );
  }
}

class _WaitingCard extends StatelessWidget {
  const _WaitingCard();
  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Kicker('Account in attesa di attivazione'),
            SizedBox(height: 6),
            Text('Il tuo coach ti abiliterà a breve. Nel frattempo puoi registrare i tuoi massimali.'),
          ]),
        ),
      );
}

class _PinnedMessage extends StatelessWidget {
  final Message m;
  const _PinnedMessage(this.m);
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Ink.white, borderRadius: BorderRadius.circular(8)),
        child: Row(children: [
          const Icon(Icons.push_pin_outlined, color: Ink.black, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(m.title, style: const TextStyle(color: Ink.black, fontWeight: FontWeight.w800)),
              Text(m.body, style: const TextStyle(color: Ink.black, fontSize: 13), maxLines: 2, overflow: TextOverflow.ellipsis),
            ]),
          ),
        ]),
      );
}

class _EmptyDay extends StatelessWidget {
  final DateTime d;
  final VoidCallback? onAdded;
  const _EmptyDay(this.d, {this.onAdded});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 48),
        child: Column(children: [
          const Icon(Icons.hotel_outlined, size: 40, color: Ink.muted),
          const SizedBox(height: 12),
          const Text('Nessun allenamento programmato.', style: TextStyle(color: Ink.muted)),
          const SizedBox(height: 24),
          Text(DemoData.restDay[d.day % DemoData.restDay.length],
              textAlign: TextAlign.center, style: const TextStyle(fontSize: 12, letterSpacing: 2, fontWeight: FontWeight.w800, color: Ink.muted)),
          if (session.isStaff) ...[
            const SizedBox(height: 32),
            OutlinedButton.icon(
              onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: d))).then((_) => onAdded?.call()),
              icon: const Icon(Icons.add),
              label: const Text('AGGIUNGI ALLENAMENTO'),
            ),
          ],
        ]),
      );
}

class _WorkoutCard extends StatelessWidget {
  final Workout w;
  const _WorkoutCard(this.w);

  @override
  Widget build(BuildContext context) {
    final lines = w.description.split('\n').where((l) => l.trim().isNotEmpty).toList();
    final preview = lines.take(6).toList();
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutDetailScreen(w))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              Tag(w.format, filled: true),
              const SizedBox(width: 6),
              if (w.audience == 'assigned') const Tag('Dedicato'),
              if (w.audience == 'personal') const Tag('Personale'),
              const Spacer(),
              const Icon(Icons.chevron_right, color: Ink.muted),
            ]),
            const SizedBox(height: 10),
            Text(w.name, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            if (w.lines != null) StructuredLines(w.lines!, maxLines: 6) else ...[
              for (final l in preview) Padding(padding: const EdgeInsets.only(bottom: 2), child: Text(l, style: const TextStyle(fontSize: 14, color: Color(0xFFD6D6D6)))),
              if (lines.length > preview.length) const Padding(padding: EdgeInsets.only(top: 4), child: Text('…', style: TextStyle(color: Ink.muted))),
            ],
            if (w.ranges.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Divider(),
              const SizedBox(height: 10),
              for (final g in w.ranges) PercentRow(g),
            ],
          ]),
        ),
      ),
    );
  }
}

class PercentRow extends StatelessWidget {
  final RangeGroup g;
  const PercentRow(this.g, {super.key});
  @override
  Widget build(BuildContext context) {
    final m = DemoData.currentMax(g.exercise);
    if (m == null) {
      return Row(children: [
        const Icon(Icons.info_outline, size: 16, color: Ink.muted),
        const SizedBox(width: 8),
        Expanded(child: Text('Massimale di ${g.exercise} non registrato. Inseriscilo per vedere i carichi.', style: const TextStyle(fontSize: 13, color: Ink.muted))),
      ]);
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('${g.exercise} · 1RM ${fmtValue(m)}', style: const TextStyle(fontSize: 12, color: Ink.muted)),
        const SizedBox(height: 4),
        Wrap(spacing: 6, runSpacing: 6, children: [
          for (final v in g.values)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
              decoration: BoxDecoration(border: Border.all(color: Ink.white), borderRadius: BorderRadius.circular(6)),
              child: RichText(
                text: TextSpan(style: const TextStyle(fontSize: 13, color: Ink.white, fontFeatures: [FontFeature.tabularFigures()]), children: [
                  TextSpan(text: '$v% ', style: const TextStyle(color: Ink.muted)),
                  TextSpan(text: fmtKg(m.value * v / 100), style: const TextStyle(fontWeight: FontWeight.w800)),
                ]),
              ),
            ),
        ]),
      ]),
    );
  }
}
