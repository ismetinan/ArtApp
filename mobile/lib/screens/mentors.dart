import 'package:flutter/material.dart';

/// Faz 2'de gerçek mentor pazarı gelecek — Faz 1'de bilinçli placeholder
/// (CLAUDE.md: mentor pazarı Faz 1 kapsam DIŞI, feature flag kapalı).
class MentorsScreen extends StatelessWidget {
  const MentorsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentorlar')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.people_outline, size: 64),
              const SizedBox(height: 16),
              Text('Mentor pazarı çok yakında!',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              const Text(
                'Şimdilik her ödevine anında ücretsiz AI analizi alabilirsin. '
                'Gerçek mentorlar bir sonraki sürümde burada olacak.',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
