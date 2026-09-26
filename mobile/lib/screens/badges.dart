import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Sunucunun gönderdiği ikon anahtarı → Material ikon. Tanınmayan anahtar
/// (yeni rozet, eski istemci) varsayılan kupaya düşer.
IconData badgeIcon(String key) => switch (key) {
      'rocket' => Icons.rocket_launch,
      'school' => Icons.school,
      'stairs' => Icons.stairs,
      'fire' => Icons.local_fire_department,
      'share' => Icons.public,
      'star' => Icons.star,
      _ => Icons.emoji_events,
    };

/// Profildeki rozet şeridi. Dokununca açıklama gösterilir.
class BadgeStrip extends StatelessWidget {
  final List<BadgeInfo> badges;
  const BadgeStrip({super.key, required this.badges});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final b in badges)
          ActionChip(
            avatar: Icon(badgeIcon(b.icon), size: 18, color: cs.primary),
            label: Text(b.title),
            onPressed: () => ScaffoldMessenger.of(context)
              ..hideCurrentSnackBar()
              ..showSnackBar(SnackBar(content: Text('${b.title}: ${b.description}'))),
          ),
      ],
    );
  }
}

/// Yeni rozet / kampanya jetonu kutlaması.
Future<void> showCelebration(BuildContext context, Celebration c) {
  final t = AppLocalizations.of(context);
  final cs = Theme.of(context).colorScheme;
  return showDialog<void>(
    context: context,
    builder: (ctx) => AlertDialog(
      icon: Icon(
        c.badges.isNotEmpty ? badgeIcon(c.badges.first.icon) : Icons.toll,
        size: 40,
        color: cs.primary,
      ),
      title: Text(c.badges.length == 1 ? c.badges.first.title : t.celebrationTitle),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (c.badges.length == 1)
            Text(c.badges.first.description)
          else
            for (final b in c.badges)
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(badgeIcon(b.icon), color: cs.primary),
                title: Text(b.title),
                subtitle: Text(b.description),
              ),
          if (c.bonusJetons > 0) ...[
            const SizedBox(height: 12),
            Text(t.launchBonusBody(c.bonusJetons),
                style: const TextStyle(fontWeight: FontWeight.w600)),
          ],
        ],
      ),
      actions: [
        FilledButton(
          onPressed: () => Navigator.of(ctx).pop(),
          child: Text(t.celebrationOk),
        ),
      ],
    ),
  );
}
