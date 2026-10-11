import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';

class MaxesScreen extends StatefulWidget {
  const MaxesScreen({super.key});
  @override
  State<MaxesScreen> createState() => _MaxesScreenState();
}

class _MaxesScreenState extends State<MaxesScreen> {
  @override
  Widget build(BuildContext context) {
    final exercises = DemoData.maxRecords.map((m) => m.key).toSet().toList();
    final byCat = <String, List<String>>{};
    for (final e in exercises) {
      byCat.putIfAbsent(DemoData.category[e] ?? 'Altro', () => []).add(e);
    }
    return Scaffold(
      appBar: AppBar(title: const Text('MASSIMALI')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        for (final cat in ['Pesistica', 'Monostrutturali', 'Corpo libero'])
          if (byCat[cat] != null) ...[
            Kicker(cat),
            const SizedBox(height: 8),
            Card(
              child: Column(children: [
                for (var i = 0; i < byCat[cat]!.length; i++) ...[
                  if (i > 0) const Divider(),
                  _MaxRow(byCat[cat]![i]),
                ],
              ]),
            ),
            const SizedBox(height: 20),
          ],
      ]),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Ink.white,
        foregroundColor: Ink.black,
        onPressed: () => _addSheet(context),
        icon: const Icon(Icons.add),
        label: const Text('NUOVO TEST', style: TextStyle(fontWeight: FontWeight.w800, letterSpacing: 1)),
      ),
    );
  }

  void _addSheet(BuildContext context) {
    String exercise = 'Back Squat';
    String type = '1RM';
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (c) => StatefulBuilder(
        builder: (c, setSt) => Padding(
          padding: EdgeInsets.fromLTRB(16, 16, 16, MediaQuery.of(c).viewInsets.bottom + 24),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text('NUOVO TEST', style: Theme.of(c).textTheme.titleLarge),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              initialValue: exercise,
              decoration: const InputDecoration(labelText: 'Esercizio'),
              dropdownColor: Ink.surface2,
              items: [for (final e in DemoData.category.keys) DropdownMenuItem(value: e, child: Text(e))],
              onChanged: (v) => setSt(() => exercise = v!),
            ),
            const SizedBox(height: 12),
            Wrap(spacing: 8, children: [
              for (final t in ['1RM', '3RM', '5RM', 'Max reps', 'Tempo'])
                ChoiceChip(
                  label: Text(t),
                  selected: type == t,
                  selectedColor: Ink.white,
                  labelStyle: TextStyle(color: type == t ? Ink.black : Ink.white),
                  onSelected: (_) => setSt(() => type = t),
                ),
            ]),
            const SizedBox(height: 12),
            const TextField(keyboardType: TextInputType.number, decoration: InputDecoration(labelText: 'Valore')),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () {
                Navigator.pop(c);
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Test registrato.')));
              },
              child: const Text('SALVA'),
            ),
          ]),
        ),
      ),
    );
  }
}

class _MaxRow extends StatelessWidget {
  final String exercise;
  const _MaxRow(this.exercise);
  @override
  Widget build(BuildContext context) {
    final h = DemoData.history(exercise);
    final cur = h.last;
    final prev = h.length > 1 ? h[h.length - 2] : null;
    final better = cur.unit == 'pace' || cur.unit == 'min' ? (prev != null && cur.value < prev.value) : (prev != null && cur.value > prev.value);
    return ListTile(
      onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MaxHistoryScreen(exercise))),
      title: Text(exercise, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text('${cur.testType} · ${fmtDateMed(cur.date)}', style: const TextStyle(color: Ink.muted, fontSize: 12)),
      trailing: Row(mainAxisSize: MainAxisSize.min, children: [
        if (prev != null) Icon(better ? Icons.trending_up : Icons.trending_flat, size: 18, color: Ink.muted),
        const SizedBox(width: 8),
        Text(fmtValue(cur), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
        const SizedBox(width: 4),
        const Icon(Icons.chevron_right, color: Ink.muted),
      ]),
    );
  }
}

class MaxHistoryScreen extends StatelessWidget {
  final String exercise;
  const MaxHistoryScreen(this.exercise, {super.key});
  @override
  Widget build(BuildContext context) {
    final h = DemoData.history(exercise);
    final first = h.first, last = h.last;
    final delta = last.value - first.value;
    final pct = first.value == 0 ? 0 : delta / first.value * 100;
    final minV = h.map((m) => m.value).reduce((a, b) => a < b ? a : b);
    final maxV = h.map((m) => m.value).reduce((a, b) => a > b ? a : b);
    return Scaffold(
      appBar: AppBar(title: Text(exercise.toUpperCase())),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Row(children: [
          Expanded(child: _Big('Attuale', fmtValue(last))),
          Expanded(child: _Big('Dal primo test', '${delta >= 0 ? '+' : ''}${delta.toStringAsFixed(1).replaceAll('.0', '')} (${pct.toStringAsFixed(1).replaceAll('.', ',')}%)')),
        ]),
        const SizedBox(height: 20),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 20, 20, 12),
            child: SizedBox(
              height: 220,
              child: LineChart(LineChartData(
                minY: minV - (maxV - minV) * 0.4 - 1,
                maxY: maxV + (maxV - minV) * 0.4 + 1,
                gridData: FlGridData(show: true, drawVerticalLine: false, getDrawingHorizontalLine: (_) => const FlLine(color: Ink.line, strokeWidth: 1)),
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(),
                  rightTitles: const AxisTitles(),
                  leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 40, getTitlesWidget: (v, _) => Text(v.toStringAsFixed(0), style: const TextStyle(fontSize: 10, color: Ink.muted)))),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 1,
                      getTitlesWidget: (v, _) {
                        final i = v.round();
                        if (i < 0 || i >= h.length) return const SizedBox();
                        return Padding(padding: const EdgeInsets.only(top: 6), child: Text(fmtDateShort(h[i].date), style: const TextStyle(fontSize: 10, color: Ink.muted)));
                      },
                    ),
                  ),
                ),
                lineBarsData: [
                  LineChartBarData(
                    spots: [for (var i = 0; i < h.length; i++) FlSpot(i.toDouble(), h[i].value)],
                    color: Ink.white,
                    barWidth: 2,
                    dotData: FlDotData(show: true, getDotPainter: (_, __, ___, ____) => FlDotCirclePainter(radius: 4, color: Ink.black, strokeColor: Ink.white, strokeWidth: 2)),
                  ),
                ],
              )),
            ),
          ),
        ),
        const SizedBox(height: 20),
        const Kicker('Storico'),
        const SizedBox(height: 8),
        Card(
          child: Column(children: [
            for (var i = h.length - 1; i >= 0; i--) ...[
              if (i < h.length - 1) const Divider(),
              ListTile(
                title: Text(fmtValue(h[i]), style: const TextStyle(fontWeight: FontWeight.w800)),
                subtitle: Text('${h[i].testType} · ${fmtDateMed(h[i].date)}', style: const TextStyle(color: Ink.muted, fontSize: 12)),
                trailing: h[i].value == maxV ? const Tag('PR', filled: true) : null,
              ),
            ],
          ]),
        ),
      ]),
    );
  }
}

class _Big extends StatelessWidget {
  final String label, value;
  const _Big(this.label, this.value);
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Kicker(label),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
      ]);
}
