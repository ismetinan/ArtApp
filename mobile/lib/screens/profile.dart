import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import '../main.dart';
import 'admin_panel.dart';
import 'auth_form.dart';
import 'mentor_panel.dart';
import 'onboarding.dart';
import 'redline.dart';
import 'store.dart';

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
                  // Dokununca ileri seviyelerin yol haritası açılır (müşteri isteği)
                  ActionChip(
                    label: Text(t.levelBadge(p['level'] as int, p['xp'] as int)),
                    avatar: const Icon(Icons.military_tech, size: 18),
                    onPressed: () => _showLevelRoadmap(context, p),
                  ),
                  Wrap(spacing: 8, children: [
                    if (ApiClient.instance.mentorMarketEnabled)
                      // Billing açıkken jeton çipi mağazaya götürür
                      ActionChip(
                        label: Text(
                            t.jetonBalance((p['jeton_balance'] ?? 0) as int)),
                        avatar: const Icon(Icons.toll, size: 18),
                        onPressed: ApiClient.instance.billingEnabled
                            ? () => _openStore(context, p)
                            : null,
                      ),
                    if (p['is_premium'] == true)
                      Chip(
                        label: Text(t.premiumBadge),
                        avatar: const Icon(Icons.workspace_premium, size: 18),
                      ),
                  ]),
                ]),
              ]),
              const SizedBox(height: 16),
              Text(t.abilityChartTitle,
                  style: Theme.of(context).textTheme.titleMedium),
              Text(t.abilityChartHint),
              const SizedBox(height: 8),
              if (chart.isEmpty)
                // Atlayanlar için geri dönüş yolu: karta dokun → seviye belirleme
                Card(
                  child: ListTile(
                    contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 4),
                    title: Text(t.chartEmpty),
                    subtitle: Text(t.chartEmptyCta),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => Navigator.of(context).push(MaterialPageRoute(
                        builder: (_) => const PickImagesScreen())),
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
                                submissionId: item['submission_id'] as int,
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
              if (ApiClient.instance.mentorMarketEnabled) ...[
                const SizedBox(height: 24),
                _MentorSection(
                  mentor: p['mentor'] as Map<String, dynamic>?,
                  gallery: gallery,
                  onChanged: () =>
                      setState(() => _future = ApiClient.instance.getProfile()),
                ),
                const SizedBox(height: 16),
                const _MyRequestsSection(),
                if (p['is_admin'] == true) ...[
                  const SizedBox(height: 16),
                  Card(
                    child: ListTile(
                      leading: const Icon(Icons.admin_panel_settings_outlined),
                      title: Text(t.adminSectionTitle),
                      subtitle: Text(t.adminSectionBody),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                            builder: (_) => const AdminPanelScreen()),
                      ),
                    ),
                  ),
                ],
              ],
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
              const SizedBox(height: 16),
              // Karanlık tema anahtarı: yalnız cihaz-yerel tercih, sunucuya yazılmaz
              SwitchListTile(
                secondary: const Icon(Icons.dark_mode_outlined),
                title: Text(t.darkModeTitle),
                subtitle: Text(t.darkModeSubtitle),
                value: ApiClient.instance.darkMode,
                onChanged: (value) async {
                  await ApiClient.instance.setDarkMode(value);
                  appThemeMode.value = value ? ThemeMode.dark : ThemeMode.light;
                  setState(() {});
                },
              ),
              const SizedBox(height: 32),
              // Beta geri bildirim kanalı: hazır şablonla e-posta uygulamasını açar
              ListTile(
                leading: const Icon(Icons.feedback_outlined),
                title: Text(t.feedbackButton),
                subtitle: Text(t.sendFeedbackBody),
                onTap: () => _sendFeedback(context),
              ),
              ListTile(
                leading: const Icon(Icons.logout),
                title: Text(t.signOut),
                onTap: () => _confirmSignOut(context),
              ),
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

  Future<void> _sendFeedback(BuildContext context) async {
    final t = AppLocalizations.of(context);
    final info = await PackageInfo.fromPlatform();
    final uri = Uri(
      scheme: 'mailto',
      path: 'ismet17inan@gmail.com',
      query: Uri(queryParameters: {
        'subject': t.feedbackMailSubject,
        'body': t.feedbackMailBody('${info.version}+${info.buildNumber}'),
      }).query,
    );
    try {
      await launchUrl(uri);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(t.errorUnexpected)));
      }
    }
  }

  void _showLevelRoadmap(BuildContext context, Map<String, dynamic> p) {
    final t = AppLocalizations.of(context);
    final current = p['level'] as int;
    final perLevel = (p['xp_per_level'] ?? 100) as int;
    // Mevcut seviyenin birkaç üstüne kadar göster — "ileri seviyeler" hissi
    final maxLevel = current + 5;
    showModalBottomSheet<void>(
      context: context,
      builder: (ctx) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.all(16),
          children: [
            Text(t.levelRoadmapTitle, style: Theme.of(ctx).textTheme.titleMedium),
            const SizedBox(height: 8),
            for (var lvl = 1; lvl <= maxLevel; lvl++)
              ListTile(
                dense: true,
                leading: Icon(
                  lvl < current
                      ? Icons.check_circle
                      : lvl == current
                          ? Icons.radio_button_checked
                          : Icons.radio_button_off,
                  color: lvl <= current ? Theme.of(ctx).colorScheme.primary : null,
                ),
                title: Text(t.levelRoadmapEntry(lvl, (lvl - 1) * perLevel)),
                trailing: lvl == current
                    ? Chip(
                        label: Text(t.levelRoadmapCurrent),
                        visualDensity: VisualDensity.compact,
                      )
                    : null,
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _openStore(BuildContext context, Map<String, dynamic> p) async {
    final bought = await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => StoreScreen(
          isPremium: p['is_premium'] == true,
          premiumUntil: p['premium_until'] as String?,
        ),
      ),
    );
    if (bought == true && mounted) {
      setState(() => _future = ApiClient.instance.getProfile());
    }
  }

  Future<void> _confirmSignOut(BuildContext context) async {
    final t = AppLocalizations.of(context);
    // Misafir hesaba tekrar girilemez (şifresi yok) — çıkış = kalıcı kayıp
    final body = ApiClient.instance.isGuest
        ? t.signOutGuestBody
        : t.signOutConfirmBody;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(t.signOutConfirmTitle),
        content: Text(body),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false), child: Text(t.cancel)),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: Text(t.signOut)),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    await ApiClient.instance.logout();
    if (context.mounted) {
      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const WelcomeScreen()),
        (_) => false,
      );
    }
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

/// Bildirim derin bağlantısı hedefi: "Mentor İsteklerim" tek başına ekran
/// (cevap geldi / iade bildirimine dokununca açılır).
class MyRequestsScreen extends StatelessWidget {
  const MyRequestsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(AppLocalizations.of(context).myRequestsTitle)),
      body: const SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: _MyRequestsSection(),
      ),
    );
  }
}

/// Faz 2: profildeki mentor bölümü — başvuru / bekleme / panel girişi.
class _MentorSection extends StatelessWidget {
  final Map<String, dynamic>? mentor;
  final List gallery;
  final VoidCallback onChanged;
  const _MentorSection(
      {required this.mentor, required this.gallery, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final status = mentor?['status'] as String?;

    if (status == 'approved') {
      return Card(
        child: ListTile(
          leading: const Icon(Icons.school),
          title: Text(t.mentorPanelTitle),
          trailing: const Icon(Icons.chevron_right),
          onTap: () => Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => MentorPanelScreen(
                initialAvailable: (mentor?['is_available'] ?? true) as bool),
          )),
        ),
      );
    }
    if (status == 'pending') {
      return Card(
        child: ListTile(
          leading: const Icon(Icons.hourglass_top),
          title: Text(t.mentorApplyPending),
        ),
      );
    }
    // hiç başvuru yok ya da reddedildi → (yeniden) başvuru
    return Card(
      child: ListTile(
        leading: const Icon(Icons.school_outlined),
        title: Text(t.becomeMentor),
        subtitle: Text(
            status == 'rejected' ? t.mentorApplyRejected : t.becomeMentorBody),
        trailing: const Icon(Icons.chevron_right),
        onTap: () async {
          final applied = await Navigator.of(context).push<bool>(
            MaterialPageRoute(builder: (_) => MentorApplyScreen(gallery: gallery)),
          );
          if (applied == true) onChanged();
        },
      ),
    );
  }
}

/// Faz 2: mentor başvuru formu — bio + stil seçimi + galeriden portfolyo.
class MentorApplyScreen extends StatefulWidget {
  final List gallery;
  const MentorApplyScreen({super.key, required this.gallery});

  @override
  State<MentorApplyScreen> createState() => _MentorApplyScreenState();
}

class _MentorApplyScreenState extends State<MentorApplyScreen> {
  final _bio = TextEditingController();
  final Set<String> _styles = {};
  final Set<int> _portfolio = {};
  bool _busy = false;

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      await ApiClient.instance
          .applyMentor(_bio.text.trim(), _styles.toList(), _portfolio.toList());
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(t.mentorApplyTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          TextField(
            controller: _bio,
            maxLines: 3,
            decoration: InputDecoration(
              labelText: t.mentorBioLabel,
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          Text(t.mentorStylesLabel,
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              for (final e in styles.entries)
                FilterChip(
                  label: Text(e.value),
                  selected: _styles.contains(e.key),
                  onSelected: (sel) => setState(() =>
                      sel ? _styles.add(e.key) : _styles.remove(e.key)),
                ),
            ],
          ),
          if (widget.gallery.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(t.mentorPortfolioPick,
                style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            GridView.count(
              crossAxisCount: 3,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              children: [
                for (final item in widget.gallery)
                  GestureDetector(
                    onTap: () => setState(() {
                      final sid = item['submission_id'] as int;
                      _portfolio.contains(sid)
                          ? _portfolio.remove(sid)
                          : _portfolio.add(sid);
                    }),
                    child: Stack(fit: StackFit.expand, children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(
                          ApiClient.instance
                              .imageUrl(item['submission_id'] as int),
                          headers: ApiClient.instance.authHeaders,
                          fit: BoxFit.cover,
                          errorBuilder: (_, _, _) => const Icon(Icons.image),
                        ),
                      ),
                      if (_portfolio.contains(item['submission_id'] as int))
                        const Align(
                          alignment: Alignment.topRight,
                          child: Padding(
                            padding: EdgeInsets.all(4),
                            child: Icon(Icons.check_circle, color: Colors.green),
                          ),
                        ),
                    ]),
                  ),
              ],
            ),
          ],
          const SizedBox(height: 24),
          _busy
              ? const Center(child: CircularProgressIndicator())
              : FilledButton(
                  onPressed: _submit, child: Text(t.mentorApplySubmit)),
        ],
      ),
    );
  }
}

/// Faz 2: öğrencinin mentor istekleri — durum + gelen geri bildirim + puanlama.
class _MyRequestsSection extends StatefulWidget {
  const _MyRequestsSection();

  @override
  State<_MyRequestsSection> createState() => _MyRequestsSectionState();
}

class _MyRequestsSectionState extends State<_MyRequestsSection> {
  late Future<List<MentorRequestInfo>> _future;

  @override
  void initState() {
    super.initState();
    _future = ApiClient.instance.getMyMentorRequests();
  }

  void _reload() =>
      setState(() => _future = ApiClient.instance.getMyMentorRequests());

  Future<void> _rate(MentorRequestInfo r, int rating) async {
    try {
      await ApiClient.instance.rateMentorRequest(r.id, rating);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context).ratedThanks)));
      }
      _reload();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return FutureBuilder(
      future: _future,
      builder: (context, snapshot) {
        final requests = snapshot.data ?? const <MentorRequestInfo>[];
        if (requests.isEmpty) return const SizedBox.shrink();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(t.myRequestsTitle,
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            for (final r in requests)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Icon(
                          switch (r.status) {
                            'answered' => Icons.check_circle,
                            'expired' => Icons.timer_off,
                            _ => Icons.pending_outlined,
                          },
                          size: 18,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            '${r.nodeId ?? t.homeworkFallback}'
                            '${r.mentorDisplayName != null ? ' • ${r.mentorDisplayName}' : ''}',
                            style: Theme.of(context).textTheme.titleSmall,
                          ),
                        ),
                        Text(
                          switch (r.status) {
                            'answered' => t.requestStatusAnswered,
                            'expired' => t.requestStatusExpired,
                            _ => t.requestStatusAssigned,
                          },
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ]),
                      if (r.status == 'answered') ...[
                        const SizedBox(height: 8),
                        Text(t.mentorFeedbackTitle,
                            style: Theme.of(context).textTheme.bodySmall),
                        Text(r.feedbackText),
                        const SizedBox(height: 4),
                        if (r.rating == null)
                          Row(children: [
                            Text('${t.rateFeedback}: '),
                            for (var star = 1; star <= 5; star++)
                              IconButton(
                                visualDensity: VisualDensity.compact,
                                icon: const Icon(Icons.star_border, size: 20),
                                onPressed: () => _rate(r, star),
                              ),
                          ])
                        else
                          Row(children: [
                            for (var star = 1; star <= 5; star++)
                              Icon(
                                star <= r.rating!
                                    ? Icons.star
                                    : Icons.star_border,
                                size: 18,
                                color: Colors.amber,
                              ),
                          ]),
                      ],
                    ],
                  ),
                ),
              ),
          ],
        );
      },
    );
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
