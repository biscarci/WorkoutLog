import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart' hide Ink;
import '../theme.dart';

/// Simulatore di fascia cardiaca: genera un battito plausibile.
class HeartRateSim {
  static final HeartRateSim instance = HeartRateSim._();
  HeartRateSim._();
  final _ctrl = StreamController<int>.broadcast();
  Timer? _t;
  double _bpm = 72;
  bool working = false;
  bool connected = true;
  final int maxHr = 190;
  final List<int> samples = [];
  final List<int> zoneSeconds = [0, 0, 0, 0, 0];

  Stream<int> get stream => _ctrl.stream;
  int get bpm => _bpm.round();

  void start() {
    _t ??= Timer.periodic(const Duration(seconds: 1), (_) {
      final r = Random();
      final target = working ? 150 + r.nextInt(25) : 70 + r.nextInt(8);
      _bpm += (target - _bpm) * 0.08 + (r.nextDouble() - 0.5) * 2;
      final b = _bpm.round();
      if (working) {
        samples.add(b);
        zoneSeconds[zoneIndex(b)]++;
      }
      _ctrl.add(b);
    });
  }

  void beginWorkout() {
    working = true;
    samples.clear();
    for (var i = 0; i < 5; i++) zoneSeconds[i] = 0;
  }

  void endWorkout() => working = false;

  int zoneIndex(int b) {
    final p = b / maxHr;
    if (p < 0.6) return 0;
    if (p < 0.7) return 1;
    if (p < 0.8) return 2;
    if (p < 0.9) return 3;
    return 4;
  }

  int get avg => samples.isEmpty ? 0 : samples.reduce((a, b) => a + b) ~/ samples.length;
  int get maxSeen => samples.isEmpty ? 0 : samples.reduce(max);
}

class CardioPanel extends StatefulWidget {
  final bool compact;
  const CardioPanel({super.key, required this.compact});
  @override
  State<CardioPanel> createState() => _CardioPanelState();
}

class _CardioPanelState extends State<CardioPanel> {
  final sim = HeartRateSim.instance;
  late StreamSubscription sub;
  int bpm = 72;

  @override
  void initState() {
    super.initState();
    sim.start();
    bpm = sim.bpm;
    sub = sim.stream.listen((b) => setState(() => bpm = b));
  }

  @override
  void dispose() {
    sub.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final z = sim.zoneIndex(bpm);
    final zc = Ink.zones[z];
    final pct = (bpm / sim.maxHr * 100).round();
    if (widget.compact) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        decoration: BoxDecoration(color: zc.withValues(alpha: 0.18), border: Border.all(color: zc), borderRadius: BorderRadius.circular(8)),
        child: Row(children: [
          Icon(Icons.favorite, color: zc, size: 22),
          const SizedBox(width: 10),
          Text('$bpm', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800, fontFeatures: [FontFeature.tabularFigures()])),
          const SizedBox(width: 4),
          const Text('bpm', style: TextStyle(color: Ink.muted)),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(color: zc, borderRadius: BorderRadius.circular(4)),
            child: Text('Z${z + 1}', style: const TextStyle(color: Ink.black, fontWeight: FontWeight.w800)),
          ),
          const SizedBox(width: 10),
          Text('$pct%', style: const TextStyle(color: Ink.muted)),
        ]),
      );
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Kicker('Fascia cardiaca'),
            const Spacer(),
            Container(width: 8, height: 8, decoration: BoxDecoration(shape: BoxShape.circle, color: sim.connected ? Ink.white : Ink.muted)),
            const SizedBox(width: 6),
            Text(sim.connected ? 'Polar H10 connessa' : 'Non connessa', style: const TextStyle(fontSize: 12, color: Ink.muted)),
          ]),
          const SizedBox(height: 12),
          Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
            Icon(Icons.favorite, color: zc, size: 30),
            const SizedBox(width: 10),
            Text('$bpm', style: const TextStyle(fontSize: 44, fontWeight: FontWeight.w800, height: 1, fontFeatures: [FontFeature.tabularFigures()])),
            const SizedBox(width: 6),
            const Padding(padding: EdgeInsets.only(bottom: 6), child: Text('bpm', style: TextStyle(color: Ink.muted))),
            const Spacer(),
            Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(color: zc, borderRadius: BorderRadius.circular(6)),
                child: Text('ZONA ${z + 1}', style: const TextStyle(color: Ink.black, fontWeight: FontWeight.w800, letterSpacing: 1)),
              ),
              const SizedBox(height: 4),
              Text('$pct% della FC max', style: const TextStyle(fontSize: 12, color: Ink.muted)),
            ]),
          ]),
          const SizedBox(height: 14),
          Row(children: [
            for (var i = 0; i < 5; i++)
              Expanded(
                child: Container(
                  height: 6,
                  margin: EdgeInsets.only(right: i < 4 ? 3 : 0),
                  decoration: BoxDecoration(color: i <= z ? Ink.zones[i] : Ink.line, borderRadius: BorderRadius.circular(3)),
                ),
              ),
          ]),
          const SizedBox(height: 10),
          const Row(children: [
            Icon(Icons.battery_5_bar, size: 16, color: Ink.muted),
            SizedBox(width: 4),
            Text('78%', style: TextStyle(fontSize: 12, color: Ink.muted)),
            SizedBox(width: 16),
            Text('FC max 190 · a riposo 58', style: TextStyle(fontSize: 12, color: Ink.muted)),
          ]),
        ]),
      ),
    );
  }
}

class ZoneBars extends StatelessWidget {
  final List<int> seconds;
  const ZoneBars(this.seconds, {super.key});
  @override
  Widget build(BuildContext context) {
    final total = seconds.fold<int>(0, (a, b) => a + b);
    return Column(children: [
      for (var i = 0; i < 5; i++)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Row(children: [
            SizedBox(width: 28, child: Text('Z${i + 1}', style: TextStyle(fontWeight: FontWeight.w800, color: Ink.zones[i]))),
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(3),
                child: LinearProgressIndicator(value: total == 0 ? 0 : seconds[i] / total, minHeight: 8, backgroundColor: Ink.line, color: Ink.zones[i]),
              ),
            ),
            const SizedBox(width: 10),
            SizedBox(width: 44, child: Text('${seconds[i] ~/ 60}:${(seconds[i] % 60).toString().padLeft(2, '0')}', textAlign: TextAlign.right, style: const TextStyle(fontSize: 12, color: Ink.muted))),
          ]),
        ),
    ]);
  }
}
