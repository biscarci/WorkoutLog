import 'package:flutter/material.dart' hide Ink;
import 'package:flutter/services.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'data.dart';
import 'theme.dart';
import 'screens/today.dart';
import 'screens/progress.dart';
import 'screens/maxes.dart';
import 'screens/profile.dart';
import 'screens/coach.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(statusBarColor: Colors.transparent, systemNavigationBarColor: Colors.black));
  await DemoData.load();
  runApp(const LiftoffApp());
}

class Session extends ChangeNotifier {
  Role role = Role.athlete;
  bool enabled = true;
  String name = 'Marina';
  String username = 'Mellux';
  bool loggedIn = false;
  bool hrBand = true;

  void login(Role r) {
    role = r;
    loggedIn = true;
    switch (r) {
      case Role.athlete:
        name = 'Marina';
        username = 'Mellux';
      case Role.coach:
        name = 'Valerio';
        username = 'COACH VALE';
      case Role.superuser:
        name = 'Biagio';
        username = 'biscarci';
    }
    notifyListeners();
  }

  void logout() {
    loggedIn = false;
    notifyListeners();
  }

  bool get isStaff => role != Role.athlete;
}

final session = Session();

class LiftoffApp extends StatelessWidget {
  const LiftoffApp({super.key});
  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: session,
      builder: (context, _) => MaterialApp(
        title: 'LIFTOFF',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: session.loggedIn ? const Shell() : const LoginScreen(),
      ),
    );
  }
}

class Logo extends StatelessWidget {
  final double width;
  const Logo({super.key, this.width = 180});
  @override
  Widget build(BuildContext context) => SvgPicture.asset('assets/logo.svg', width: width);
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final user = TextEditingController();
  final pass = TextEditingController();

  void _go(Role r) {
    session.login(r);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 440),
            child: ListView(
              padding: const EdgeInsets.symmetric(horizontal: 28, vertical: 24),
              children: [
                const SizedBox(height: 40),
                const Center(child: Logo(width: 220)),
                const SizedBox(height: 56),
                TextField(controller: user, decoration: const InputDecoration(labelText: 'Username o email')),
                const SizedBox(height: 12),
                TextField(controller: pass, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
                const SizedBox(height: 8),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton(
                    onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Se l\'indirizzo è registrato riceverai un\'email con le istruzioni.'))),
                    child: const Text('Password dimenticata?'),
                  ),
                ),
                const SizedBox(height: 8),
                FilledButton(onPressed: () => _go(Role.athlete), child: const Text('ACCEDI')),
                const SizedBox(height: 28),
                const Center(child: Kicker('Demo · entra come')),
                const SizedBox(height: 10),
                Row(children: [
                  Expanded(child: OutlinedButton(onPressed: () => _go(Role.athlete), child: const Text('ATLETA'))),
                  const SizedBox(width: 8),
                  Expanded(child: OutlinedButton(onPressed: () => _go(Role.coach), child: const Text('COACH'))),
                  const SizedBox(width: 8),
                  Expanded(child: OutlinedButton(onPressed: () => _go(Role.superuser), child: const Text('SUPER'))),
                ]),
                const SizedBox(height: 32),
                const Center(child: Text('Non hai un account? Chiedi al tuo coach un invito.', style: TextStyle(color: Ink.muted, fontSize: 13))),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class Shell extends StatefulWidget {
  const Shell({super.key});
  @override
  State<Shell> createState() => _ShellState();
}

class _ShellState extends State<Shell> {
  int index = 0;

  @override
  Widget build(BuildContext context) {
    final staff = session.isStaff;
    final pages = <Widget>[
      const TodayScreen(),
      const ProgressScreen(),
      const MaxesScreen(),
      if (staff) const CoachScreen(),
      const ProfileScreen(),
    ];
    final dests = <NavigationDestination>[
      const NavigationDestination(icon: Icon(Icons.today_outlined), selectedIcon: Icon(Icons.today), label: 'OGGI'),
      const NavigationDestination(icon: Icon(Icons.show_chart), selectedIcon: Icon(Icons.show_chart), label: 'PROGRESSI'),
      const NavigationDestination(icon: Icon(Icons.fitness_center_outlined), selectedIcon: Icon(Icons.fitness_center), label: 'MASSIMALI'),
      if (staff) const NavigationDestination(icon: Icon(Icons.sports_outlined), selectedIcon: Icon(Icons.sports), label: 'COACH'),
      const NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'PROFILO'),
    ];
    if (index >= pages.length) index = 0;
    return Scaffold(
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(border: Border(top: BorderSide(color: Ink.line))),
        child: NavigationBar(selectedIndex: index, onDestinationSelected: (i) => setState(() => index = i), destinations: dests),
      ),
    );
  }
}
