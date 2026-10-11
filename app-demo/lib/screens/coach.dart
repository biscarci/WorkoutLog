import 'package:flutter/material.dart' hide Ink;
import '../data.dart';
import '../theme.dart';
import '../main.dart';
import 'editor.dart';

class CoachScreen extends StatelessWidget {
  const CoachScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final su = session.role == Role.superuser;
    return DefaultTabController(
      length: su ? 5 : 4,
      child: Scaffold(
        appBar: AppBar(
          title: Text(su ? 'AMMINISTRAZIONE' : 'COACH'),
          bottom: TabBar(isScrollable: true, tabAlignment: TabAlignment.start, tabs: [
            const Tab(text: 'PROGRAMMAZIONE'),
            const Tab(text: 'ATLETI'),
            const Tab(text: 'MESSAGGI'),
            const Tab(text: 'LOG'),
            if (su) const Tab(text: 'ACCOUNT'),
          ]),
        ),
        body: TabBarView(children: [
          const _WeekGrid(),
          const _Athletes(),
          const _Broadcast(),
          const _Log(),
          if (su) const _Accounts(),
        ]),
      ),
    );
  }
}

class _WeekGrid extends StatefulWidget {
  const _WeekGrid();
  @override
  State<_WeekGrid> createState() => _WeekGridState();
}

class _WeekGridState extends State<_WeekGrid> {
  DateTime monday = DateTime(2026, 9, 14);
  bool published = true;

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
        child: Row(children: [
          IconButton(onPressed: () => setState(() => monday = monday.subtract(const Duration(days: 7))), icon: const Icon(Icons.chevron_left)),
          Expanded(child: Center(child: Text('${fmtDateShort(monday)} – ${fmtDateShort(monday.add(const Duration(days: 6)))}', style: Theme.of(context).textTheme.titleMedium))),
          IconButton(onPressed: () => setState(() => monday = monday.add(const Duration(days: 7))), icon: const Icon(Icons.chevron_right)),
        ]),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16),
        child: Row(children: [
          Tag(published ? 'Pubblicata' : 'Bozza', filled: published),
          const Spacer(),
          TextButton.icon(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ImportTextScreen(monday: monday))).then((_) => setState(() {})),
            icon: const Icon(Icons.paste, size: 16),
            label: const Text('INSERISCI ESERCIZI DA TESTO'),
          ),
          TextButton.icon(onPressed: () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Settimana copiata sulla successiva (demo).'))), icon: const Icon(Icons.content_copy, size: 16), label: const Text('')),

        ]),
      ),
      Expanded(
        child: ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 90),
          itemCount: 7,
          itemBuilder: (context, i) {
            final d = monday.add(Duration(days: i));
            final ws = DemoData.forDay(d).where((w) => w.audience == 'all').toList();
            return Padding(
              padding: const EdgeInsets.only(bottom: 14),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Row(children: [
                  Text('${weekdaysLong[i]} ${d.day}'.toUpperCase(), style: Theme.of(context).textTheme.labelSmall),
                  const Spacer(),
                  IconButton(
                    visualDensity: VisualDensity.compact,
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: d))).then((_) => setState(() {})),
                    icon: const Icon(Icons.add_circle_outline, size: 22, color: Ink.white),
                  ),
                ]),
                if (ws.isEmpty)
                  Container(
                    height: 44,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(border: Border.all(color: Ink.line), borderRadius: BorderRadius.circular(8)),
                    child: const Text('Rest day', style: TextStyle(color: Ink.muted, fontSize: 13)),
                  )
                else
                  Card(
                    child: Column(children: [
                      for (var j = 0; j < ws.length; j++) ...[
                        if (j > 0) const Divider(),
                        ListTile(
                          dense: true,
                          leading: const Icon(Icons.drag_indicator, color: Ink.muted),
                          title: Text(ws[j].name, style: const TextStyle(fontWeight: FontWeight.w700)),
                          subtitle: Text(ws[j].description.split('\n').first, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(color: Ink.muted, fontSize: 12)),
                          trailing: Tag(ws[j].format),
                          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorkoutEditorScreen(date: d, existing: ws[j]))).then((_) => setState(() {})),
                        ),
                      ],
                    ]),
                  ),
              ]),
            );
          },
        ),
      ),
    ]);
  }
}

class _Athletes extends StatelessWidget {
  const _Athletes();
  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(16), children: [
      FilledButton.icon(
        onPressed: () => _invite(context),
        icon: const Icon(Icons.mail_outline),
        label: const Text('INVITA ATLETA'),
      ),
      const SizedBox(height: 16),
      const Kicker('Inviti pendenti'),
      const SizedBox(height: 8),
      const Card(
        child: ListTile(
          leading: Icon(Icons.hourglass_empty, color: Ink.muted),
          title: Text('giorgio.fini@example.it'),
          subtitle: Text('Inviato 2 giorni fa · scade tra 5 giorni', style: TextStyle(color: Ink.muted, fontSize: 12)),
          trailing: Icon(Icons.more_vert, color: Ink.muted),
        ),
      ),
      const SizedBox(height: 20),
      const Kicker('Atleti'),
      const SizedBox(height: 8),
      Card(
        child: Column(children: [
          for (var i = 0; i < DemoData.athletes.length; i++) ...[
            if (i > 0) const Divider(),
            _AthleteRow(DemoData.athletes[i]),
          ],
        ]),
      ),
    ]);
  }

  void _invite(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (c) => Padding(
        padding: EdgeInsets.fromLTRB(16, 16, 16, MediaQuery.of(c).viewInsets.bottom + 24),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text('INVITA ATLETA', style: Theme.of(c).textTheme.titleLarge),
          const SizedBox(height: 6),
          const Text('Riceverà un\'email con il link per installare l\'app e creare l\'account, già abilitato.', style: TextStyle(color: Ink.muted, fontSize: 13)),
          const SizedBox(height: 16),
          const TextField(keyboardType: TextInputType.emailAddress, decoration: InputDecoration(labelText: 'Email')),
          const SizedBox(height: 10),
          const Row(children: [
            Expanded(child: TextField(decoration: InputDecoration(labelText: 'Nome (facoltativo)'))),
            SizedBox(width: 10),
            Expanded(child: TextField(decoration: InputDecoration(labelText: 'Cognome'))),
          ]),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () {
              Navigator.pop(c);
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Invito inviato.')));
            },
            child: const Text('INVIA INVITO'),
          ),
        ]),
      ),
    );
  }
}

class _AthleteRow extends StatelessWidget {
  final Athlete a;
  const _AthleteRow(this.a);
  @override
  Widget build(BuildContext context) {
    final icon = switch (a.trend) { 'up' => Icons.trending_up, 'down' => Icons.trending_down, _ => Icons.trending_flat };
    return ListTile(
      onTap: () {},
      title: Text(a.name, style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text(
        a.enabled ? 'Ultimo accesso ${a.lastSeenDays == 0 ? 'oggi' : '${a.lastSeenDays} gg fa'} · ${a.workouts30} WOD in 30 gg' : 'In attesa di attivazione',
        style: TextStyle(color: a.lastSeenDays > 14 ? Ink.white : Ink.muted, fontSize: 12),
      ),
      trailing: a.enabled
          ? Icon(icon, color: Ink.muted)
          : OutlinedButton(
              style: OutlinedButton.styleFrom(minimumSize: const Size(0, 36), padding: const EdgeInsets.symmetric(horizontal: 12)),
              onPressed: () => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${a.name} abilitato.'))),
              child: const Text('ABILITA', style: TextStyle(fontSize: 12)),
            ),
    );
  }
}

class _Broadcast extends StatefulWidget {
  const _Broadcast();
  @override
  State<_Broadcast> createState() => _BroadcastState();
}

class _BroadcastState extends State<_Broadcast> {
  final title = TextEditingController();
  final body = TextEditingController();
  String to = 'Tutti gli atleti';
  bool pin = false;

  @override
  Widget build(BuildContext context) {
    return ListView(padding: const EdgeInsets.all(16), children: [
      const Kicker('Nuovo messaggio'),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: to,
        dropdownColor: Ink.surface2,
        decoration: const InputDecoration(labelText: 'Destinatari'),
        items: const [
          DropdownMenuItem(value: 'Tutti gli atleti', child: Text('Tutti gli atleti abilitati (23)')),
          DropdownMenuItem(value: 'Gruppo', child: Text('Gruppo: Competitors (6)')),
          DropdownMenuItem(value: 'Singolo', child: Text('Singolo atleta…')),
        ],
        onChanged: (v) => setState(() => to = v!),
      ),
      const SizedBox(height: 10),
      TextField(controller: title, decoration: const InputDecoration(labelText: 'Titolo')),
      const SizedBox(height: 10),
      TextField(controller: body, maxLines: 4, decoration: const InputDecoration(labelText: 'Testo')),
      const SizedBox(height: 4),
      SwitchListTile(contentPadding: EdgeInsets.zero, value: pin, onChanged: (v) => setState(() => pin = v), title: const Text('Fissa in cima alla schermata Oggi')),
      const SizedBox(height: 8),
      FilledButton.icon(
        onPressed: () {
          if (title.text.isEmpty) return;
          setState(() {
            DemoData.messages.insert(0, Message(title.text, body.text, DateTime.now(), pinned: pin));
            title.clear();
            body.clear();
            pin = false;
          });
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Messaggio inviato: push a 23 atleti.')));
        },
        icon: const Icon(Icons.send),
        label: const Text('INVIA'),
      ),
      const SizedBox(height: 24),
      const Kicker('Inviati'),
      const SizedBox(height: 8),
      for (final m in DemoData.messages) ...[
        Card(
          child: ListTile(
            title: Text(m.title, style: const TextStyle(fontWeight: FontWeight.w700)),
            subtitle: Text('${fmtDateShort(m.date)} · letto da ${14 + m.title.length % 8} su 23', style: const TextStyle(color: Ink.muted, fontSize: 12)),
            trailing: m.pinned ? const Icon(Icons.push_pin_outlined, size: 18, color: Ink.muted) : null,
          ),
        ),
        const SizedBox(height: 8),
      ],
    ]);
  }
}

class _Log extends StatefulWidget {
  const _Log();
  @override
  State<_Log> createState() => _LogState();
}

class _LogState extends State<_Log> {
  String filter = 'Tutti';
  @override
  Widget build(BuildContext context) {
    final su = session.role == Role.superuser;
    var rows = DemoData.log;
    if (!su) rows = rows.where((l) => l.role != 'superuser' && !l.action.startsWith('login')).toList();
    if (filter != 'Tutti') rows = rows.where((l) => l.role == filter.toLowerCase()).toList();
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
        child: Row(children: [
          for (final f in ['Tutti', 'Coach', 'Atleta', if (su) 'Superuser']) ...[
            ChoiceChip(
              label: Text(f.toUpperCase()),
              selected: filter == f,
              selectedColor: Ink.white,
              labelStyle: TextStyle(color: filter == f ? Ink.black : Ink.white, fontSize: 11, fontWeight: FontWeight.w800),
              onSelected: (_) => setState(() => filter = f),
            ),
            const SizedBox(width: 6),
          ],
        ]),
      ),
      Expanded(
        child: ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: rows.length,
          separatorBuilder: (_, __) => const Divider(),
          itemBuilder: (context, i) {
            final l = rows[i];
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 8),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                SizedBox(
                  width: 58,
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(fmtDateShort(l.at), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                    Text('${l.at.hour}:${l.at.minute.toString().padLeft(2, '0')}', style: const TextStyle(fontSize: 11, color: Ink.muted)),
                  ]),
                ),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      Text(l.user, style: const TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(width: 6),
                      Tag(l.role),
                    ]),
                    const SizedBox(height: 2),
                    Text(l.action, style: const TextStyle(fontFamily: 'monospace', fontSize: 12, color: Ink.muted)),
                    Text(l.target, style: const TextStyle(fontSize: 13)),
                  ]),
                ),
              ]),
            );
          },
        ),
      ),
    ]);
  }
}

class _Accounts extends StatelessWidget {
  const _Accounts();
  @override
  Widget build(BuildContext context) {
    final rows = [
      ('Biagio Scarciello', 'biscarci', Role.superuser),
      ('Valerio Steman', 'COACH VALE', Role.coach),
      for (final a in DemoData.athletes) (a.name, a.username, Role.athlete),
    ];
    return ListView(padding: const EdgeInsets.all(16), children: [
      Row(children: [
        Expanded(child: OutlinedButton.icon(onPressed: () {}, icon: const Icon(Icons.person_add_alt), label: const Text('INVITA COACH'))),
        const SizedBox(width: 10),
        Expanded(child: OutlinedButton.icon(onPressed: () {}, icon: const Icon(Icons.download), label: const Text('EXPORT'))),
      ]),
      const SizedBox(height: 20),
      const Kicker('Tutti gli account'),
      const SizedBox(height: 8),
      Card(
        child: Column(children: [
          for (var i = 0; i < rows.length; i++) ...[
            if (i > 0) const Divider(),
            ListTile(
              title: Text(rows[i].$1, style: const TextStyle(fontWeight: FontWeight.w700)),
              subtitle: Text('@${rows[i].$2}', style: const TextStyle(color: Ink.muted, fontSize: 12)),
              trailing: Row(mainAxisSize: MainAxisSize.min, children: [
                Tag(rows[i].$3.label, filled: rows[i].$3 != Role.athlete),
                const SizedBox(width: 6),
                const Icon(Icons.more_vert, color: Ink.muted),
              ]),
              onTap: () {},
            ),
          ],
        ]),
      ),
      const SizedBox(height: 20),
      const Kicker('Impostazioni del box'),
      const SizedBox(height: 8),
      const Card(
        child: Column(children: [
          ListTile(leading: Icon(Icons.store_outlined), title: Text('Nome e logo'), trailing: Icon(Icons.chevron_right, color: Ink.muted)),
          Divider(),
          ListTile(leading: Icon(Icons.format_quote_outlined), title: Text('Frasi motivazionali'), subtitle: Text('112 attive · 8 disattivate', style: TextStyle(color: Ink.muted, fontSize: 12)), trailing: Icon(Icons.chevron_right, color: Ink.muted)),
          Divider(),
          ListTile(leading: Icon(Icons.favorite_outline), title: Text('Zone cardiache di default'), trailing: Icon(Icons.chevron_right, color: Ink.muted)),
          Divider(),
          ListTile(leading: Icon(Icons.email_outlined), title: Text('Template email e canale di contatto'), trailing: Icon(Icons.chevron_right, color: Ink.muted)),
        ]),
      ),
    ]);
  }
}
