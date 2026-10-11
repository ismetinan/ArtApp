import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// AI ödevi kartı. Yapılandırılmış hâli varsa bölümlere ayrılır (amaç, numaralı
/// adımlar, kontrol listesi, süre) — düz metinden çok daha kolay okunuyor ve
/// kontrol listesi AI'ın uyum analizinde baktığı maddelerin aynısı. Eski
/// ödevlerde yalnız metin vardır, o zaman olduğu gibi gösterilir.
class AssignmentCard extends StatelessWidget {
  final String? text;
  final AssignmentBrief? brief;
  const AssignmentCard({super.key, this.text, this.brief});

  @override
  Widget build(BuildContext context) {
    final b = brief;
    if (b == null || b.steps.isEmpty) {
      return Card(
        child: Padding(padding: const EdgeInsets.all(12), child: Text(text ?? '')),
      );
    }
    final t = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final label = theme.textTheme.labelLarge?.copyWith(color: cs.primary);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(child: Text(t.assignmentGoal, style: label)),
            if (b.timeMinutes > 0)
              Chip(
                visualDensity: VisualDensity.compact,
                avatar: const Icon(Icons.schedule, size: 16),
                label: Text(t.assignmentTime(b.timeMinutes)),
              ),
          ]),
          Text(b.goal, style: theme.textTheme.bodyLarge),
          const SizedBox(height: 12),
          Text(t.assignmentSteps, style: label),
          const SizedBox(height: 4),
          for (var i = 0; i < b.steps.length; i++)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                CircleAvatar(
                  radius: 11,
                  backgroundColor: cs.primaryContainer,
                  child: Text('${i + 1}',
                      style: TextStyle(fontSize: 12, color: cs.onPrimaryContainer)),
                ),
                const SizedBox(width: 10),
                Expanded(child: Text(b.steps[i])),
              ]),
            ),
          if (b.criteria.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(t.assignmentChecklist, style: label),
            const SizedBox(height: 2),
            Text(t.assignmentChecklistHint, style: theme.textTheme.bodySmall),
            const SizedBox(height: 4),
            for (final c in b.criteria)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Icon(Icons.check_box_outline_blank, size: 20, color: cs.outline),
                  const SizedBox(width: 10),
                  Expanded(child: Text(c)),
                ]),
              ),
          ],
        ]),
      ),
    );
  }
}
