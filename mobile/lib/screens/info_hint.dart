import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Sekme başındaki kısa açıklama kartı ("bu ekran ne işe yarar").
/// [prefsKey] verilirse ✕ ile kapatılabilir ve kapatıldığı cihazda bir daha
/// görünmez; verilmezse kalıcıdır (ör. kilitli bir özelliği anlatan not).
class InfoHint extends StatefulWidget {
  final IconData icon;
  final String text;
  final String? prefsKey;
  final EdgeInsetsGeometry margin;

  const InfoHint({
    super.key,
    required this.icon,
    required this.text,
    this.prefsKey,
    this.margin = const EdgeInsets.fromLTRB(12, 8, 12, 0),
  });

  @override
  State<InfoHint> createState() => _InfoHintState();
}

class _InfoHintState extends State<InfoHint> {
  // Kapatılabilir kartlar tercih okunana kadar gizli: açılışta bir an görünüp
  // kaybolmasın
  late bool _hidden = widget.prefsKey != null;

  @override
  void initState() {
    super.initState();
    final key = widget.prefsKey;
    if (key == null) return;
    SharedPreferences.getInstance().then((prefs) {
      if (mounted) setState(() => _hidden = prefs.getBool(key) ?? false);
    }).catchError((_) {
      if (mounted) setState(() => _hidden = false);
    });
  }

  Future<void> _dismiss() async {
    setState(() => _hidden = true);
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(widget.prefsKey!, true);
    } catch (_) {/* yalnız kolaylık tercihi */}
  }

  @override
  Widget build(BuildContext context) {
    if (_hidden) return const SizedBox.shrink();
    final cs = Theme.of(context).colorScheme;
    return Padding(
      padding: widget.margin,
      child: Card(
        margin: EdgeInsets.zero,
        color: cs.secondaryContainer,
        child: Padding(
          padding: EdgeInsets.fromLTRB(12, 10, widget.prefsKey == null ? 12 : 0, 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(widget.icon, size: 20, color: cs.onSecondaryContainer),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  widget.text,
                  style: Theme.of(context)
                      .textTheme
                      .bodySmall
                      ?.copyWith(color: cs.onSecondaryContainer),
                ),
              ),
              if (widget.prefsKey != null)
                IconButton(
                  visualDensity: VisualDensity.compact,
                  icon: const Icon(Icons.close, size: 18),
                  tooltip: MaterialLocalizations.of(context).closeButtonTooltip,
                  onPressed: _dismiss,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
