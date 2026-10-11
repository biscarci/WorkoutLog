import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';

class ProgressScreen extends StatefulWidget {
  const ProgressScreen({super.key});
  @override
  State<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends State<ProgressScreen> {
  int period = 1; // 0 = 30gg, 1 = 90gg, 2 = 1 anno

  @override
  Widget build(BuildContext context) {
    final weeks = [3, 4, 2, 4, 5, 3, 4, 4, 3, 5, 4, 2];
    final shown = period == 0 ? weeks.sublist(8) : (period == 1 ? weeks.sublist(0) : weeks);
    final zones = [12, 48, 95, 62, 18];
    return Scaffold(
      appBar: AppBar(title: const Text('PROGRESSI')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Row(children: [
          for (var i = 0; i < 3; i++) ...[
            ChoiceChip(
              label: Text(['30 GIORNI', '90 GIORNI', '1 ANNO'][i]),
              selected: period == i,
              selectedColor: Ink.white,
              labelStyle: TextStyle(color: period == i ? Ink.black : Ink.white, fontSize: 11, fontWeight: FontWeight.w800),
              onSelected: (_) => setState(() => period = i),
            ),
            const SizedBox(width: 8),
          ],
        ]),
        const SizedBox(height: 20),
        Row(children: const [
          Expanded(child: _Tile('Allenamenti', '43', '+6 vs periodo prec.')),
          SizedBox(width: 10),
          Expanded(child: _Tile('Costanza', '9 sett.', 'di fila con ≥ 1 WOD')),
          SizedBox(width: 10),
          Expanded(child: _Tile('PR', '4', 'ultimo: Deadlift 155')),
        ]),
        const SizedBox(height: 24),
        const Kicker('Allenamenti per settimana'),
        const SizedBox(height: 10),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(8, 20, 16, 8),
            child: SizedBox(
              height: 160,
              child: BarChart(BarChartData(
                maxY: 6,
                gridData: const FlGridData(show: false),
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(),
                  rightTitles: const AxisTitles(),
                  leftTitles: const AxisTitles(),
                  bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, getTitlesWidget: (v, _) => Padding(padding: const EdgeInsets.only(top: 4), child: Text('S${v.toInt() + 1}', style: const TextStyle(fontSize: 10, color: Ink.muted))))),
                ),
                barGroups: [
                  for (var i = 0; i < shown.length; i++)
                    BarChartGroupData(x: i, barRods: [BarChartRodData(toY: shown[i].toDouble(), color: i == shown.length - 1 ? Ink.white : Ink.muted, width: 14, borderRadius: BorderRadius.circular(3))]),
                ],
              )),
            ),
          ),
        ),
        const SizedBox(height: 24),
        const Kicker('Andamento massimali'),
        const SizedBox(height: 10),
        Card(
          child: Column(children: [
            for (final e in ['Back Squat', 'Deadlift', 'Squat Snatch', 'Bench Press']) ...[
              if (e != 'Back Squat') const Divider(),
              _TrendRow(e),
            ],
          ]),
        ),
        const SizedBox(height: 24),
        const Kicker('Benchmark ripetuti'),
        const SizedBox(height: 10),
        const Card(
          child: Column(children: [
            _BenchRow('Fran', '5:12', '5:48', true),
            Divider(),
            _BenchRow('Grace', '3:41', '3:35', false),
            Divider(),
            _BenchRow('Cindy', '19 round + 4', '17 round + 11', true),
          ]),
        ),
        const SizedBox(height: 24),
        const Kicker('Minuti per zona cardiaca'),
        const SizedBox(height: 10),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(children: [
              for (var i = 0; i < 5; i++)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(children: [
                    SizedBox(width: 28, child: Text('Z${i + 1}', style: TextStyle(fontWeight: FontWeight.w800, color: Ink.zones[i]))),
                    Expanded(child: ClipRRect(borderRadius: BorderRadius.circular(3), child: LinearProgressIndicator(value: zones[i] / 100, minHeight: 8, backgroundColor: Ink.line, color: Ink.zones[i]))),
                    const SizedBox(width: 10),
                    SizedBox(width: 44, child: Text('${zones[i]} min', textAlign: TextAlign.right, style: const TextStyle(fontSize: 12, color: Ink.muted))),
                  ]),
                ),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Tile extends StatelessWidget {
  final String label, value, sub;
  const _Tile(this.label, this.value, this.sub);
  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Kicker(label),
            const SizedBox(height: 6),
            Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
            const SizedBox(height: 2),
            Text(sub, style: const TextStyle(fontSize: 11, color: Ink.muted)),
          ]),
        ),
      );
}

class _TrendRow extends StatelessWidget {
  final String e;
  const _TrendRow(this.e);
  @override
  Widget build(BuildContext context) {
    final h = DemoData.history(e);
    final d = h.last.value - h.first.value;
    final pct = d / h.first.value * 100;
    return ListTile(
      title: Text(e, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text('${h.length} test · ${fmtDateMed(h.first.date)} → ${fmtDateMed(h.last.date)}', style: const TextStyle(fontSize: 12, color: Ink.muted)),
      trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
        Text(fmtValue(h.last), style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
        Text('${d >= 0 ? '+' : ''}${d.toStringAsFixed(1).replaceAll('.0', '')} kg · ${pct.toStringAsFixed(1).replaceAll('.', ',')}%', style: const TextStyle(fontSize: 11, color: Ink.muted)),
      ]),
    );
  }
}

class _BenchRow extends StatelessWidget {
  final String name, last, prev;
  final bool better;
  const _BenchRow(this.name, this.last, this.prev, this.better);
  @override
  Widget build(BuildContext context) => ListTile(
        title: Text(name, style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('precedente $prev', style: const TextStyle(fontSize: 12, color: Ink.muted)),
        trailing: Row(mainAxisSize: MainAxisSize.min, children: [
          Icon(better ? Icons.trending_up : Icons.trending_down, size: 18, color: Ink.muted),
          const SizedBox(width: 8),
          Text(last, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16, fontFeatures: [FontFeature.tabularFigures()])),
          if (better) ...[const SizedBox(width: 8), const Tag('PR', filled: true)],
        ]),
      );
}
