import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';

class MessagesScreen extends StatefulWidget {
  const MessagesScreen({super.key});
  @override
  State<MessagesScreen> createState() => _MessagesScreenState();
}

class _MessagesScreenState extends State<MessagesScreen> {
  @override
  Widget build(BuildContext context) {
    final msgs = DemoData.messages;
    return Scaffold(
      appBar: AppBar(title: const Text('MESSAGGI')),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: msgs.length,
        separatorBuilder: (_, __) => const SizedBox(height: 10),
        itemBuilder: (context, i) {
          final m = msgs[i];
          return Card(
            child: InkWell(
              borderRadius: BorderRadius.circular(8),
              onTap: () => setState(() => m.read = true),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    if (!m.read) Container(width: 8, height: 8, margin: const EdgeInsets.only(right: 8), decoration: const BoxDecoration(color: Ink.white, shape: BoxShape.circle)),
                    Expanded(child: Text(m.title, style: TextStyle(fontWeight: m.read ? FontWeight.w600 : FontWeight.w800, fontSize: 16))),
                    if (m.pinned) const Icon(Icons.push_pin_outlined, size: 16, color: Ink.muted),
                  ]),
                  const SizedBox(height: 4),
                  Text('Coach Vale · ${fmtDateShort(m.date)} ${m.date.hour}:${m.date.minute.toString().padLeft(2, '0')}', style: const TextStyle(fontSize: 12, color: Ink.muted)),
                  const SizedBox(height: 8),
                  Text(m.body),
                ]),
              ),
            ),
          );
        },
      ),
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
          child: OutlinedButton.icon(
            onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Apre il canale scelto dal box (WhatsApp, email, telefono).'))),
            icon: const Icon(Icons.chat_bubble_outline),
            label: const Text('CONTATTA IL COACH'),
          ),
        ),
      ),
    );
  }
}
