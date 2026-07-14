import 'dart:io';

import 'package:flutter/material.dart';

import '../api.dart';

const _severityColors = {
  'dusuk': Color(0xFFF0C020),
  'orta': Color(0xFFF07020),
  'yuksek': Color(0xFFE02020),
};

/// AI redline sonucu: çizim + koordinatlı bulgu işaretleri + yapıcı notlar
class RedlineScreen extends StatelessWidget {
  final String imagePath;
  final RedlineResult analysis;
  final int xpAwarded;

  const RedlineScreen({
    super.key,
    required this.imagePath,
    required this.analysis,
    required this.xpAwarded,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI Analizi')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (xpAwarded > 0)
            Card(
              color: Theme.of(context).colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(children: [
                  const Icon(Icons.stars),
                  const SizedBox(width: 8),
                  Text('+$xpAwarded XP kazandın!',
                      style: Theme.of(context).textTheme.titleMedium),
                ]),
              ),
            ),
          const SizedBox(height: 8),
          AspectRatio(
            aspectRatio: 3 / 4,
            child: LayoutBuilder(
              builder: (context, constraints) => Stack(
                fit: StackFit.expand,
                children: [
                  Image.file(File(imagePath), fit: BoxFit.contain),
                  for (var i = 0; i < analysis.findings.length; i++)
                    Positioned(
                      left: analysis.findings[i].x * constraints.maxWidth - 14,
                      top: analysis.findings[i].y * constraints.maxHeight - 14,
                      child: _Marker(index: i + 1, finding: analysis.findings[i]),
                    ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text('Güçlü yönlerin', style: Theme.of(context).textTheme.titleMedium),
          for (final s in analysis.strengthsTr)
            ListTile(
              dense: true,
              leading: const Icon(Icons.thumb_up, color: Colors.green),
              title: Text(s),
            ),
          const SizedBox(height: 8),
          Text('Gelişim noktaları', style: Theme.of(context).textTheme.titleMedium),
          for (var i = 0; i < analysis.findings.length; i++)
            Card(
              child: ListTile(
                leading: CircleAvatar(
                  radius: 14,
                  backgroundColor:
                      _severityColors[analysis.findings[i].severity],
                  child: Text('${i + 1}',
                      style: const TextStyle(color: Colors.white, fontSize: 12)),
                ),
                title: Text(analysis.findings[i].messageTr),
                subtitle: Text('Öneri: ${analysis.findings[i].suggestionTr}'),
              ),
            ),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Text(analysis.overallCommentTr,
                  style: Theme.of(context).textTheme.bodyLarge),
            ),
          ),
        ],
      ),
    );
  }
}

class _Marker extends StatelessWidget {
  final int index;
  final RedlineFinding finding;
  const _Marker({required this.index, required this.finding});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: _severityColors[finding.severity]!, width: 3),
        color: Colors.white.withValues(alpha: 0.7),
      ),
      alignment: Alignment.center,
      child: Text('$index', style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }
}
