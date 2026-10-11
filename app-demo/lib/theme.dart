import 'package:flutter/material.dart';

class Ink {
  static const black = Color(0xFF000000);
  static const white = Color(0xFFFFFFFF);
  static const surface1 = Color(0xFF111111);
  static const surface2 = Color(0xFF1C1C1C);
  static const line = Color(0xFF2E2E2E);
  static const muted = Color(0xFF9A9A9A);
  static const danger = Color(0xFFA50404);
  // Zone cardiache: unica eccezione al bianco e nero
  static const zones = [Color(0xFF8A8A8A), Color(0xFF3B82F6), Color(0xFF22C55E), Color(0xFFF97316), Color(0xFFEF4444)];
}

ThemeData buildTheme() {
  const scheme = ColorScheme(
    brightness: Brightness.dark,
    primary: Ink.white,
    onPrimary: Ink.black,
    secondary: Ink.white,
    onSecondary: Ink.black,
    error: Ink.danger,
    onError: Ink.white,
    surface: Ink.black,
    onSurface: Ink.white,
    surfaceContainerHighest: Ink.surface2,
    outline: Ink.line,
  );
  final base = ThemeData(useMaterial3: true, colorScheme: scheme, scaffoldBackgroundColor: Ink.black);
  return base.copyWith(
    textTheme: base.textTheme.apply(bodyColor: Ink.white, displayColor: Ink.white).copyWith(
          headlineMedium: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, letterSpacing: 1.5),
          titleLarge: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700),
          titleMedium: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          bodyMedium: const TextStyle(fontSize: 15, height: 1.4),
          labelSmall: const TextStyle(fontSize: 11, letterSpacing: 1.2, fontWeight: FontWeight.w600, color: Ink.muted),
        ),
    appBarTheme: const AppBarTheme(
      backgroundColor: Ink.black,
      foregroundColor: Ink.white,
      elevation: 0,
      scrolledUnderElevation: 0,
      centerTitle: false,
      titleTextStyle: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, letterSpacing: 1.5, color: Ink.white),
    ),
    cardTheme: const CardThemeData(
      color: Ink.surface1,
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(8)), side: BorderSide(color: Ink.line)),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: Ink.white,
        foregroundColor: Ink.black,
        minimumSize: const Size.fromHeight(52),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, letterSpacing: 1.2),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: Ink.white,
        side: const BorderSide(color: Ink.white),
        minimumSize: const Size.fromHeight(48),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, letterSpacing: 1),
      ),
    ),
    textButtonTheme: TextButtonThemeData(style: TextButton.styleFrom(foregroundColor: Ink.white)),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Ink.surface2,
      labelStyle: const TextStyle(color: Ink.muted),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Ink.line)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Ink.line)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: Ink.white)),
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Ink.black,
      indicatorColor: Ink.white,
      height: 68,
      iconTheme: WidgetStateProperty.resolveWith((s) => IconThemeData(color: s.contains(WidgetState.selected) ? Ink.black : Ink.muted)),
      labelTextStyle: WidgetStateProperty.resolveWith((s) => TextStyle(
          fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.8, color: s.contains(WidgetState.selected) ? Ink.white : Ink.muted)),
    ),
    chipTheme: const ChipThemeData(
      backgroundColor: Ink.surface2,
      side: BorderSide(color: Ink.line),
      labelStyle: TextStyle(color: Ink.white, fontSize: 12, fontWeight: FontWeight.w600),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.all(Radius.circular(6))),
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
    ),
    dividerTheme: const DividerThemeData(color: Ink.line, space: 1),
    tabBarTheme: const TabBarThemeData(
      labelColor: Ink.white,
      unselectedLabelColor: Ink.muted,
      indicatorColor: Ink.white,
      dividerColor: Ink.line,
      labelStyle: TextStyle(fontWeight: FontWeight.w700, letterSpacing: 1),
    ),
    snackBarTheme: const SnackBarThemeData(backgroundColor: Ink.white, contentTextStyle: TextStyle(color: Ink.black, fontWeight: FontWeight.w600)),
    dialogTheme: const DialogThemeData(backgroundColor: Ink.surface1),
    bottomSheetTheme: const BottomSheetThemeData(backgroundColor: Ink.surface1),
    switchTheme: SwitchThemeData(
      thumbColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Ink.black : Ink.muted),
      trackColor: WidgetStateProperty.resolveWith((s) => s.contains(WidgetState.selected) ? Ink.white : Ink.surface2),
    ),
  );
}

/// Etichetta piccola in maiuscolo (es. categoria, sezione)
class Kicker extends StatelessWidget {
  final String text;
  const Kicker(this.text, {super.key});
  @override
  Widget build(BuildContext context) => Text(text.toUpperCase(), style: Theme.of(context).textTheme.labelSmall);
}

class Tag extends StatelessWidget {
  final String text;
  final bool filled;
  const Tag(this.text, {super.key, this.filled = false});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: filled ? Ink.white : Colors.transparent,
          border: Border.all(color: filled ? Ink.white : Ink.line),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Text(text.toUpperCase(),
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1, color: filled ? Ink.black : Ink.muted)),
      );
}

class Section extends StatelessWidget {
  final String title;
  final Widget child;
  final Widget? trailing;
  const Section({super.key, required this.title, required this.child, this.trailing});
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [Expanded(child: Kicker(title)), if (trailing != null) trailing!]),
        const SizedBox(height: 8),
        child,
      ]);
}
