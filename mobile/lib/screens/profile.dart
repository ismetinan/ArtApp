import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api.dart';

/// Profil sekmesi: seviye rozeti + tıklanabilir Ability Chart + Gelişim Macerası
/// (CLAUDE.md §7.3 — chart hem görselleştirme hem navigasyon).
class ProfileScreen extends StatefulWidget {
  final void Function(String axis) onAxisTap;
  const ProfileScreen({super.key, required this.onAxisTap});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Future<Map<String, dynamic>>? _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getProfile();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Profil'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () =>
                setState(() => _future = ApiClient.instance.getProfile()),
          ),
        ],
      ),
      body: FutureBuilder(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(child: Text('Profil yüklenemedi: ${snapshot.error}'));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final p = snapshot.data!;
          final chart = Map<String, int>.from(p['ability_chart'] as Map);
          final gallery = p['gelisim_macerasi'] as List;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Row(children: [
                const CircleAvatar(radius: 32, child: Icon(Icons.person, size: 32)),
                const SizedBox(width: 16),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(p['display_name'],
                      style: Theme.of(context).textTheme.titleLarge),
                  Chip(
                    label: Text('${p['level']}. Seviye • ${p['xp']} XP'),
                    avatar: const Icon(Icons.military_tech, size: 18),
                  ),
                ]),
              ]),
              const SizedBox(height: 16),
              Text('Ability Chart', style: Theme.of(context).textTheme.titleMedium),
              const Text('Bir eksene dokunarak ilgili derslere gidebilirsin.'),
              const SizedBox(height: 8),
              if (chart.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('Seviye belirleme tamamlanınca chart burada görünecek.'),
                  ),
                )
              else
                AspectRatio(
                  aspectRatio: 1,
                  child: AbilityChart(scores: chart, onAxisTap: widget.onAxisTap),
                ),
              const SizedBox(height: 8),
              // Oranların yazılı hali (wireframe-02'deki opsiyonel liste)
              for (final e in chart.entries)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(children: [
                    SizedBox(width: 110, child: Text(axisLabels[e.key] ?? e.key)),
                    Expanded(
                      child: LinearProgressIndicator(value: e.value / 100),
                    ),
                    SizedBox(
                        width: 52,
                        child: Text('  ${e.value}/100', textAlign: TextAlign.right)),
                  ]),
                ),
              const SizedBox(height: 24),
              Text('Gelişim Macerası',
                  style: Theme.of(context).textTheme.titleMedium),
              const Text('Yüklediğin ödevler ve AI notların, kronolojik.'),
              const SizedBox(height: 8),
              if (gallery.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text('İlk ödevini yüklediğinde maceran burada başlayacak!'),
                  ),
                ),
              for (final item in gallery)
                Card(
                  child: ListTile(
                    leading: const Icon(Icons.image),
                    title: Text(item['node_id'] ?? 'Ödev'),
                    subtitle: Text(
                      (item['ai_result']?['overall_comment_tr'] ?? '') as String,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: Switch(
                      value: item['is_public'] as bool,
                      onChanged: (v) async {
                        await ApiClient.instance
                            .setPrivacy(item['submission_id'] as int, v);
                        setState(
                            () => _future = ApiClient.instance.getProfile());
                      },
                    ),
                  ),
                ),
              if (gallery.isNotEmpty)
                const Padding(
                  padding: EdgeInsets.only(top: 4),
                  child: Text(
                    'Anahtar: açık = herkese görünür, kapalı = sadece sen (varsayılan).',
                    style: TextStyle(fontSize: 12),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

/// Radar/örümcek ağı grafiği. Eksen etiketine veya dilimine dokunulunca
/// onAxisTap tetiklenir → Dersler sekmesine yönlendirme.
class AbilityChart extends StatelessWidget {
  final Map<String, int> scores;
  final void Function(String axis) onAxisTap;
  const AbilityChart({super.key, required this.scores, required this.onAxisTap});

  @override
  Widget build(BuildContext context) {
    final axes = scores.keys.toList();
    return LayoutBuilder(
      builder: (context, constraints) => GestureDetector(
        onTapUp: (details) {
          final center = Offset(
              constraints.maxWidth / 2, constraints.maxHeight / 2);
          final v = details.localPosition - center;
          if (v.distance < 10) return;
          var angle = math.atan2(v.dy, v.dx) + math.pi / 2; // üstten başla
          if (angle < 0) angle += 2 * math.pi;
          final slice = 2 * math.pi / axes.length;
          final index = ((angle + slice / 2) % (2 * math.pi) ~/ slice);
          onAxisTap(axes[index]);
        },
        child: CustomPaint(
          painter: _RadarPainter(
            scores: scores,
            scheme: Theme.of(context).colorScheme,
            labelStyle: Theme.of(context).textTheme.bodySmall!,
          ),
        ),
      ),
    );
  }
}

class _RadarPainter extends CustomPainter {
  final Map<String, int> scores;
  final ColorScheme scheme;
  final TextStyle labelStyle;
  _RadarPainter(
      {required this.scores, required this.scheme, required this.labelStyle});

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = size.shortestSide / 2 - 40;
    final axes = scores.keys.toList();
    final n = axes.length;
    Offset point(int i, double r) {
      final angle = -math.pi / 2 + i * 2 * math.pi / n;
      return center + Offset(math.cos(angle), math.sin(angle)) * r;
    }

    final grid = Paint()
      ..style = PaintingStyle.stroke
      ..color = scheme.outlineVariant;
    for (final f in [0.25, 0.5, 0.75, 1.0]) {
      final ring = Path()..addPolygon([for (var i = 0; i < n; i++) point(i, radius * f)], true);
      canvas.drawPath(ring, grid);
    }
    for (var i = 0; i < n; i++) {
      canvas.drawLine(center, point(i, radius), grid);
    }

    final dataPath = Path()
      ..addPolygon(
          [for (var i = 0; i < n; i++) point(i, radius * scores[axes[i]]! / 100)],
          true);
    canvas.drawPath(
        dataPath,
        Paint()
          ..style = PaintingStyle.fill
          ..color = scheme.primary.withValues(alpha: 0.25));
    canvas.drawPath(
        dataPath,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2
          ..color = scheme.primary);

    for (var i = 0; i < n; i++) {
      final tp = TextPainter(
        text: TextSpan(text: axisLabels[axes[i]] ?? axes[i], style: labelStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      final p = point(i, radius + 18);
      tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) => old.scores != scores;
}
