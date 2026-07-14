import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../api.dart';
import 'home_shell.dart';

/// Onboarding ekran 1: Hoş geldin (CLAUDE.md §7.2)
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Icon(Icons.brush, size: 72),
              const SizedBox(height: 16),
              Text('ArtApp',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineLarge),
              const SizedBox(height: 8),
              Text(
                'Çizimde gelişim yolculuğun burada başlıyor.',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyLarge,
              ),
              const SizedBox(height: 48),
              // Faz 1: e-posta girişleri henüz yok; misafir akışı çekirdek döngü için yeterli
              FilledButton(
                onPressed: () => _continueAsGuest(context),
                child: const Text('Misafir Olarak Devam Et'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: null,
                child: const Text('Giriş Yap (yakında)'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: null,
                child: const Text('Kayıt Ol (yakında)'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _continueAsGuest(BuildContext context) async {
    try {
      await ApiClient.instance.createGuest('Misafir Çizer');
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Sunucuya ulaşılamadı. Backend çalışıyor mu? '
              '(docker compose up -d && uvicorn app.main:app)'),
        ));
      }
      return;
    }
    if (context.mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const PickImagesScreen()),
      );
    }
  }
}

/// Onboarding ekran 2: 3 resim belirle (kamera veya dosya)
class PickImagesScreen extends StatefulWidget {
  const PickImagesScreen({super.key});

  @override
  State<PickImagesScreen> createState() => _PickImagesScreenState();
}

class _PickImagesScreenState extends State<PickImagesScreen> {
  final _picker = ImagePicker();
  final List<XFile> _images = [];

  Future<void> _pick(ImageSource source) async {
    final file = await _picker.pickImage(source: source, maxWidth: 1600);
    if (file != null && _images.length < 3) {
      setState(() => _images.add(file));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Son 3 Çizimini Yükle')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              'Seviyeni belirlemek için son yaptığın 3 çizimi seç. '
              'Mükemmel olmaları gerekmiyor — olduğun yerden başlıyoruz.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: GridView.count(
                crossAxisCount: 3,
                mainAxisSpacing: 8,
                crossAxisSpacing: 8,
                children: [
                  for (final img in _images)
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Image.file(File(img.path), fit: BoxFit.cover),
                    ),
                  if (_images.length < 3)
                    OutlinedButton(
                      onPressed: () => _showSourceSheet(),
                      child: const Icon(Icons.add_photo_alternate, size: 32),
                    ),
                ],
              ),
            ),
            FilledButton(
              onPressed: _images.length == 3
                  ? () => Navigator.of(context).pushReplacement(MaterialPageRoute(
                      builder: (_) => AnalyzingScreen(images: _images)))
                  : null,
              child: Text('Devam Et (${_images.length}/3)'),
            ),
          ],
        ),
      ),
    );
  }

  void _showSourceSheet() {
    showModalBottomSheet(
      context: context,
      builder: (_) => SafeArea(
        child: Wrap(children: [
          ListTile(
            leading: const Icon(Icons.camera_alt),
            title: const Text('Kamera ile çek'),
            onTap: () {
              Navigator.pop(context);
              _pick(ImageSource.camera);
            },
          ),
          ListTile(
            leading: const Icon(Icons.folder),
            title: const Text('Cihazdan seç'),
            onTap: () {
              Navigator.pop(context);
              _pick(ImageSource.gallery);
            },
          ),
        ]),
      ),
    );
  }
}

/// Onboarding ekran 3: analiz bekleme
class AnalyzingScreen extends StatefulWidget {
  final List<XFile> images;
  const AnalyzingScreen({super.key, required this.images});

  @override
  State<AnalyzingScreen> createState() => _AnalyzingScreenState();
}

class _AnalyzingScreenState extends State<AnalyzingScreen> {
  @override
  void initState() {
    super.initState();
    _analyze();
  }

  Future<void> _analyze() async {
    final payload = [
      for (final img in widget.images)
        (bytes: await img.readAsBytes(), name: img.name),
    ];
    try {
      final assessment = await ApiClient.instance.assessLevel(payload);
      if (mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(builder: (_) => ResultScreen(assessment: assessment)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Analiz sırasında sorun oluştu, birazdan tekrar denenecek.')));
        await Future.delayed(const Duration(seconds: 3));
        if (mounted) _analyze();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: 24),
            Text('Resimlerin inceleniyor...',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            const Text('Bu birkaç saniye sürebilir.'),
          ],
        ),
      ),
    );
  }
}

/// Onboarding ekran 4: değerlendirme sonucu
class ResultScreen extends StatelessWidget {
  final Assessment assessment;
  const ResultScreen({super.key, required this.assessment});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Değerlendirme Sonucu')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(children: [
                  Text('${assessment.level}. Seviye',
                      style: Theme.of(context).textTheme.headlineMedium),
                  const SizedBox(height: 8),
                  Text(assessment.summaryTr),
                ]),
              ),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView(
                children: [
                  for (final e in assessment.abilityScores.entries)
                    CheckboxListTile(
                      value: true,
                      onChanged: null,
                      title: Text(axisLabels[e.key] ?? e.key),
                      subtitle: Text('${e.value}/100 — belirlendi'),
                    ),
                ],
              ),
            ),
            FilledButton(
              onPressed: () => Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const HomeShell()),
                (_) => false,
              ),
              child: const Text('Yetenek Ağacına Git'),
            ),
          ],
        ),
      ),
    );
  }
}
