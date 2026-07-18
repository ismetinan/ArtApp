import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../main.dart';
import 'auth_form.dart';
import 'onboarding.dart';
import 'redline.dart';

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
        title: Text(AppLocalizations.of(context).tabProfile),
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
            return Center(
                child: Text(AppLocalizations.of(context)
                    .profileLoadError('${snapshot.error}')));
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final p = snapshot.data!;
          final serverChart = Map<String, int>.from(p['ability_chart'] as Map);
          // Chart doluysa 7 ekseni de göster — eksikler 0 (eski backend'e karşı emniyet)
          final t = AppLocalizations.of(context);
          final labels = axisLabels(t);
          final chart = serverChart.isEmpty
              ? serverChart
              : {
                  for (final k in labels.keys) k: serverChart[k] ?? 0,
                };
          final gallery = p['gelisim_macerasi'] as List;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (ApiClient.instance.isGuest)
                Card(
                  color: Theme.of(context).colorScheme.tertiaryContainer,
                  child: ListTile(
                    leading: const Icon(Icons.shield_outlined),
                    title: Text(t.createAccountCard),
                    subtitle: Text(t.createAccountCardBody),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () async {
                      final upgraded = await Navigator.of(context).push<bool>(
                        MaterialPageRoute(
                            builder: (_) =>
                                const AuthFormScreen(mode: AuthMode.upgrade)),
                      );
                      if (upgraded == true) {
                        setState(
                            () => _future = ApiClient.instance.getProfile());
                      }
                    },
                  ),
                ),
              const SizedBox(height: 8),
              Row(children: [
                const CircleAvatar(radius: 32, child: Icon(Icons.person, size: 32)),
                const SizedBox(width: 16),
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(p['display_name'],
                      style: Theme.of(context).textTheme.titleLarge),
                  Chip(
                    label: Text(t.levelBadge(p['level'] as int, p['xp'] as int)),
                    avatar: const Icon(Icons.military_tech, size: 18),
                  ),
                ]),
              ]),
              const SizedBox(height: 16),
              Text(t.abilityChartTitle,
                  style: Theme.of(context).textTheme.titleMedium),
              Text(t.abilityChartHint),
              const SizedBox(height: 8),
              if (chart.isEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(t.chartEmpty),
                  ),
                )
              else
                AspectRatio(
                  aspectRatio: 1,
                  child: AbilityChart(
                      scores: chart,
                      labels: labels,
                      onAxisTap: widget.onAxisTap),
                ),
              const SizedBox(height: 8),
              // Oranların yazılı hali (wireframe-02'deki opsiyonel liste)
              for (final e in chart.entries)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(children: [
                    SizedBox(width: 110, child: Text(labels[e.key] ?? e.key)),
                    Expanded(
                      child: LinearProgressIndicator(value: e.value / 100),
                    ),
                    SizedBox(
                        width: 52,
                        child: Text('  ${t.scoreOutOf(e.value)}',
                            textAlign: TextAlign.right)),
                  ]),
                ),
              const SizedBox(height: 24),
              Text(t.journeyTitle,
                  style: Theme.of(context).textTheme.titleMedium),
              Text(t.journeyHint),
              const SizedBox(height: 8),
              if (gallery.isEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(t.journeyEmpty),
                  ),
                ),
              for (final item in gallery)
                Card(
                  child: ListTile(
                    leading: ClipRRect(
                      borderRadius: BorderRadius.circular(6),
                      child: Image.network(
                        ApiClient.instance
                            .imageUrl(item['submission_id'] as int),
                        headers: ApiClient.instance.authHeaders,
                        width: 48,
                        height: 48,
                        fit: BoxFit.cover,
                        errorBuilder: (_, _, _) => const Icon(Icons.image),
                      ),
                    ),
                    title: Text(item['node_id'] ?? t.homeworkFallback),
                    subtitle: Text(
                      (item['ai_result']?['overall_comment_tr'] ?? '') as String,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    onTap: item['ai_result'] == null
                        ? null
                        : () => Navigator.of(context).push(MaterialPageRoute(
                              builder: (_) => RedlineScreen(
                                image: NetworkImage(
                                  ApiClient.instance.imageUrl(
                                      item['submission_id'] as int),
                                  headers: ApiClient.instance.authHeaders,
                                ),
                                analysis: RedlineResult.fromJson(
                                    Map<String, dynamic>.from(
                                        item['ai_result'] as Map)),
                              ),
                            )),
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
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    t.privacyKeyHint,
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
              const SizedBox(height: 24),
              // Dil seçici: UI + backend hata mesajları + AI çıktı dili
              Text(t.languageTitle,
                  style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: 8),
              SegmentedButton<String>(
                segments: [
                  ButtonSegment(value: 'tr', label: Text(t.languageTurkish)),
                  ButtonSegment(value: 'en', label: Text(t.languageEnglish)),
                ],
                selected: {ApiClient.instance.language},
                onSelectionChanged: (selection) async {
                  final code = selection.first;
                  try {
                    await ApiClient.instance.setLanguage(code);
                  } catch (e) {
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(content: Text(friendlyError(context, e))));
                    }
                  }
                  // Backend'e yazılamasa bile yerel tercih geçerli — UI hemen döner
                  appLocale.value = Locale(code);
                },
              ),
              const SizedBox(height: 32),
              // Play Store şartı: hesap silme uygulama içinden erişilebilir olmalı
              ListTile(
                leading: Icon(Icons.delete_forever,
                    color: Theme.of(context).colorScheme.error),
                title: Text(t.deleteAccount,
                    style:
                        TextStyle(color: Theme.of(context).colorScheme.error)),
                subtitle: Text(t.deleteAccountBody),
                onTap: () => _confirmDelete(context),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context) async {
    final first = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(AppLocalizations.of(context).deleteConfirmTitle),
        content: Text(AppLocalizations.of(context).deleteConfirmBody),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(AppLocalizations.of(context).cancel)),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(AppLocalizations.of(context).continueButton)),
        ],
      ),
    );
    if (first != true || !context.mounted) return;
    final second = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(AppLocalizations.of(context).deleteConfirm2Title),
        content: Text(AppLocalizations.of(context).deleteConfirm2Body),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: Text(AppLocalizations.of(context).cancel)),
          FilledButton.tonal(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(AppLocalizations.of(context).deleteFinalButton)),
        ],
      ),
    );
    if (second != true || !context.mounted) return;
    try {
      await ApiClient.instance.deleteAccount();
      if (context.mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (_) => const WelcomeScreen()),
          (_) => false,
        );
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    }
  }
}

/// Radar/örümcek ağı grafiği. Eksen etiketine veya dilimine dokunulunca
/// onAxisTap tetiklenir → Dersler sekmesine yönlendirme.
class AbilityChart extends StatelessWidget {
  final Map<String, int> scores;
  final Map<String, String> labels;
  final void Function(String axis) onAxisTap;
  const AbilityChart(
      {super.key,
      required this.scores,
      required this.labels,
      required this.onAxisTap});

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
            labels: labels,
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
  final Map<String, String> labels;
  final ColorScheme scheme;
  final TextStyle labelStyle;
  _RadarPainter(
      {required this.scores,
      required this.labels,
      required this.scheme,
      required this.labelStyle});

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
        text: TextSpan(text: labels[axes[i]] ?? axes[i], style: labelStyle),
        textDirection: TextDirection.ltr,
      )..layout();
      final p = point(i, radius + 18);
      tp.paint(canvas, p - Offset(tp.width / 2, tp.height / 2));
    }
  }

  @override
  bool shouldRepaint(covariant _RadarPainter old) =>
      old.scores != scores || old.labels != labels;
}
