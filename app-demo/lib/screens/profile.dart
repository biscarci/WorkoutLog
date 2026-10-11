import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';
import '../main.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool pushWod = true, pushMsg = true, emailMsg = false, phrases = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('PROFILO')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        Row(children: [
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(color: Ink.white, borderRadius: BorderRadius.circular(8)),
            alignment: Alignment.center,
            child: Text(session.name.substring(0, 1), style: const TextStyle(color: Ink.black, fontSize: 26, fontWeight: FontWeight.w800)),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(session.name, style: Theme.of(context).textTheme.titleLarge),
              Text('@${session.username}', style: const TextStyle(color: Ink.muted)),
            ]),
          ),
          Tag(session.role.label, filled: true),
        ]),
        const SizedBox(height: 24),
        const Kicker('Account'),
        const SizedBox(height: 8),
        Card(
          child: Column(children: [
            _Row(Icons.person_outline, 'Dati personali', 'Nome, cognome, email, data di nascita'),
            const Divider(),
            _Row(Icons.lock_outline, 'Cambia password', null),
            const Divider(),
            _Row(Icons.devices_outlined, 'Dispositivi connessi', '2 sessioni attive'),
          ]),
        ),
        const SizedBox(height: 20),
        const Kicker('Fascia cardiaca e salute'),
        const SizedBox(height: 8),
        Card(
          child: Column(children: [
            SwitchListTile(
              value: session.hrBand,
              onChanged: (v) => setState(() => session.hrBand = v),
              title: const Text('Polar H10'),
              subtitle: const Text('Associata · riconnessione automatica', style: TextStyle(color: Ink.muted, fontSize: 12)),
              secondary: const Icon(Icons.bluetooth),
            ),
            const Divider(),
            _Row(Icons.favorite_outline, 'FC massima', '190 bpm · zone personalizzate'),
            const Divider(),
            _Row(Icons.watch_outlined, 'Health Connect', 'Non collegato'),
          ]),
        ),
        const SizedBox(height: 20),
        const Kicker('Notifiche'),
        const SizedBox(height: 8),
        Card(
          child: Column(children: [
            SwitchListTile(value: pushWod, onChanged: (v) => setState(() => pushWod = v), title: const Text('Programmazione pubblicata'), subtitle: const Text('Push', style: TextStyle(color: Ink.muted, fontSize: 12))),
            const Divider(),
            SwitchListTile(value: pushMsg, onChanged: (v) => setState(() => pushMsg = v), title: const Text('Messaggi del coach'), subtitle: const Text('Push', style: TextStyle(color: Ink.muted, fontSize: 12))),
            const Divider(),
            SwitchListTile(value: emailMsg, onChanged: (v) => setState(() => emailMsg = v), title: const Text('Messaggi del coach'), subtitle: const Text('Email', style: TextStyle(color: Ink.muted, fontSize: 12))),
            const Divider(),
            SwitchListTile(value: phrases, onChanged: (v) => setState(() => phrases = v), title: const Text('Frasi motivazionali'), subtitle: const Text('A fondo pagina e a fine timer', style: TextStyle(color: Ink.muted, fontSize: 12))),
          ]),
        ),
        const SizedBox(height: 20),
        const Kicker('Demo'),
        const SizedBox(height: 8),
        Card(
          child: Column(children: [
            SwitchListTile(
              value: session.enabled,
              onChanged: (v) => setState(() => session.enabled = v),
              title: const Text('Account abilitato'),
              subtitle: const Text('Disattiva per vedere la schermata di attesa', style: TextStyle(color: Ink.muted, fontSize: 12)),
            ),
          ]),
        ),
        const SizedBox(height: 28),
        OutlinedButton(onPressed: session.logout, child: const Text('ESCI')),
        const SizedBox(height: 12),
        TextButton(
          onPressed: () {},
          child: const Text('Elimina account', style: TextStyle(color: Ink.danger)),
        ),
        const SizedBox(height: 8),
        const Center(child: Text('LIFTOFF demo · v0.1', style: TextStyle(color: Ink.muted, fontSize: 12))),
      ]),
    );
  }
}

class _Row extends StatelessWidget {
  final IconData icon;
  final String title;
  final String? sub;
  const _Row(this.icon, this.title, this.sub);
  @override
  Widget build(BuildContext context) => ListTile(
        leading: Icon(icon),
        title: Text(title),
        subtitle: sub == null ? null : Text(sub!, style: const TextStyle(color: Ink.muted, fontSize: 12)),
        trailing: const Icon(Icons.chevron_right, color: Ink.muted),
        onTap: () {},
      );
}
