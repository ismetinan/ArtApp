import 'package:flutter/material.dart';

import '../l10n/gen/app_localizations.dart';

/// Faz 2'de gerçek mentor pazarı gelecek — Faz 1'de bilinçli placeholder
/// (CLAUDE.md: mentor pazarı Faz 1 kapsam DIŞI, feature flag kapalı).
class MentorsScreen extends StatelessWidget {
  const MentorsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.tabMentors)),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.people_outline, size: 64),
              const SizedBox(height: 16),
              Text(t.mentorsComingTitle,
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text(t.mentorsComingBody, textAlign: TextAlign.center),
            ],
          ),
        ),
      ),
    );
  }
}
