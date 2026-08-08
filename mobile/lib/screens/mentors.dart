import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import 'store.dart';

/// Backend'deki MAX_OPEN_REQUESTS ile aynı — yalnız bilgilendirme metninde.
const _maxOpenRequests = 3;

/// Mentorlar sekmesi (CLAUDE.md §7.5): stil filtresi + mentor kartları.
/// mentor_market_enabled kapalıysa Faz 1 placeholder'ı gösterilir.
class MentorsScreen extends StatefulWidget {
  const MentorsScreen({super.key});

  @override
  State<MentorsScreen> createState() => _MentorsScreenState();
}

class _MentorsScreenState extends State<MentorsScreen> {
  Future<List<MentorInfo>>? _future;
  String? _style;
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (ApiClient.instance.mentorMarketEnabled) _load();
  }

  void _load() => setState(() => _future =
      ApiClient.instance.getMentors(style: _style, query: _search.text.trim()));

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    if (!ApiClient.instance.mentorMarketEnabled) {
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

    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(t.tabMentors)),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
            child: TextField(
              controller: _search,
              textInputAction: TextInputAction.search,
              onSubmitted: (_) => _load(),
              decoration: InputDecoration(
                hintText: t.mentorSearchHint,
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _search.clear();
                    _load();
                  },
                ),
                border: const OutlineInputBorder(),
                isDense: true,
              ),
            ),
          ),
          SizedBox(
            height: 56,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(t.mentorStyleAll),
                    selected: _style == null,
                    onSelected: (_) {
                      _style = null;
                      _load();
                    },
                  ),
                ),
                for (final e in styles.entries)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(e.value),
                      selected: _style == e.key,
                      onSelected: (_) {
                        _style = e.key;
                        _load();
                      },
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: FutureBuilder(
              future: _future,
              builder: (context, snapshot) {
                if (snapshot.hasError) {
                  return Center(
                      child: Text(friendlyError(context, snapshot.error!)));
                }
                if (!snapshot.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final mentors = snapshot.data!;
                if (mentors.isEmpty) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(32),
                      child: Text(t.mentorsEmpty, textAlign: TextAlign.center),
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async => _load(),
                  child: ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      for (final m in mentors) _MentorCard(mentor: m),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _MentorCard extends StatelessWidget {
  final MentorInfo mentor;
  const _MentorCard({required this.mentor});

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Card(
      child: ListTile(
        leading: mentor.portfolioSubmissionIds.isEmpty
            ? const CircleAvatar(child: Icon(Icons.person))
            : ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: Image.network(
                  ApiClient.instance.imageUrl(mentor.portfolioSubmissionIds.first),
                  headers: ApiClient.instance.authHeaders,
                  width: 48,
                  height: 48,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const Icon(Icons.image),
                ),
              ),
        title: Text(mentor.displayName),
        subtitle: Text(
          [
            if (mentor.styles.isNotEmpty)
              mentor.styles.map((s) => styles[s] ?? s).join(', '),
            if (mentor.bio.isNotEmpty) mentor.bio,
          ].join(' • '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (mentor.rating != null)
              Row(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.star, size: 16, color: Colors.amber),
                Text(' ${mentor.rating!.toStringAsFixed(1)}'),
              ]),
            Text(t.mentorAnsweredCount(mentor.answeredCount),
                style: Theme.of(context).textTheme.bodySmall),
          ],
        ),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => MentorProfileScreen(mentor: mentor)),
        ),
      ),
    );
  }
}

/// Mentor profili (CLAUDE.md §7.6): ad, stiller, bio, portfolyo + "Soru sor"
/// (Faz 3: 3 jetonla doğrudan bu mentora gönderim).
class MentorProfileScreen extends StatefulWidget {
  final MentorInfo mentor;
  const MentorProfileScreen({super.key, required this.mentor});

  @override
  State<MentorProfileScreen> createState() => _MentorProfileScreenState();
}

class _MentorProfileScreenState extends State<MentorProfileScreen> {
  /// Liste yanıtı bağış alanlarını BİLİNÇLİ olarak taşımıyor (yalnız detay ucu
  /// döndürüyor), bu yüzden detay ayrıca çekilir. Gelene kadar liste verisi
  /// gösterilir — ekran boş kalmaz.
  MentorInfo? _detail;
  MentorInfo get mentor => _detail ?? widget.mentor;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
    try {
      final full = await ApiClient.instance.getMentor(widget.mentor.id);
      if (mounted) setState(() => _detail = full);
    } catch (_) {
      // Detay çekilemezse liste verisiyle devam — bağış kartı görünmez, o kadar.
    }
  }

  /// Kullanıcının ödevlerini listeler; seçilen çizim bu mentora 3 jetonla gider.
  Future<void> _askMentor() async {
    setState(() => _busy = true);
    List gallery;
    try {
      final profile = await ApiClient.instance.getProfile();
      gallery = profile['gelisim_macerasi'] as List;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
        setState(() => _busy = false);
      }
      return;
    }
    if (!mounted) return;
    setState(() => _busy = false);
    final t = AppLocalizations.of(context);
    if (gallery.isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(t.mentorNoDrawings)));
      return;
    }
    final sid = await showModalBottomSheet<int>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(t.mentorPickDrawing,
                  style: Theme.of(ctx).textTheme.titleMedium),
            ),
            SizedBox(
              height: 120,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  for (final item in gallery)
                    Padding(
                      padding: const EdgeInsets.only(right: 8, bottom: 12),
                      child: GestureDetector(
                        onTap: () => Navigator.pop(
                            ctx, item['submission_id'] as int),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.network(
                            ApiClient.instance
                                .imageUrl(item['submission_id'] as int),
                            headers: ApiClient.instance.authHeaders,
                            width: 100,
                            height: 100,
                            fit: BoxFit.cover,
                            errorBuilder: (_, _, _) =>
                                const SizedBox(
                                    width: 100, child: Icon(Icons.image)),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
    if (sid == null || !mounted) return;
    setState(() => _busy = true);
    try {
      final result = await ApiClient.instance
          .requestMentor(sid, mentorProfileId: mentor.id);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context)
                .mentorAskSent(result.mentorName))));
      }
    } catch (e) {
      if (mounted) showErrorWithStoreAction(context, e);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final styles = styleLabels(t);
    return Scaffold(
      appBar: AppBar(title: Text(mentor.displayName)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(children: [
            const CircleAvatar(radius: 32, child: Icon(Icons.person, size: 32)),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(mentor.displayName,
                      style: Theme.of(context).textTheme.titleLarge),
                  if (mentor.rating != null)
                    Row(children: [
                      const Icon(Icons.star, size: 16, color: Colors.amber),
                      Text(
                          ' ${mentor.rating!.toStringAsFixed(1)} • ${t.mentorAnsweredCount(mentor.answeredCount)}'),
                    ]),
                ],
              ),
            ),
          ]),
          const SizedBox(height: 12),
          if (mentor.styles.isNotEmpty)
            Wrap(
              spacing: 8,
              children: [
                for (final s in mentor.styles) Chip(label: Text(styles[s] ?? s)),
              ],
            ),
          if (mentor.bio.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text(mentor.bio),
          ],
          // Bağış kartı bio'dan hemen SONRA, ödeme bloğundan önce: iOS'ta
          // billingEnabled false olduğu için aşağıdaki blok hiç çizilmiyor,
          // bağış kartının oradan bağımsız olması gerekiyor.
          if (mentor.donationUrl != null) ...[
            const SizedBox(height: 16),
            _DonationCard(
              url: mentor.donationUrl!,
              platform: mentor.donationPlatform ?? '',
            ),
          ],
          const SizedBox(height: 16),
          if (ApiClient.instance.jetonAiEconomy) ...[
            // Yeni ekonomi: mentorluk ücretsiz, kotalar bedelin yerini aldı
            JetonPaymentInfo(
              title: t.mentorFreeTitle,
              body: t.mentorFreeInfo(_maxOpenRequests),
            ),
            const SizedBox(height: 8),
            _busy
                ? const Center(child: CircularProgressIndicator())
                : FilledButton.icon(
                    icon: const Icon(Icons.support_agent),
                    label: Text(t.mentorAskDirectFree),
                    onPressed: mentor.isAvailable ? _askMentor : null,
                  ),
          ] else if (ApiClient.instance.billingEnabled) ...[
            // Eski ekonomi: seçmeli mentorluk altın jetonla ödenir; mağaza
            // kapalıyken (iOS) altın edinmenin yolu yok, butonu göstermiyoruz.
            JetonPaymentInfo(
                title: t.jetonPaymentTitle, body: t.mentorDirectPaymentInfo),
            const SizedBox(height: 8),
            _busy
                ? const Center(child: CircularProgressIndicator())
                : FilledButton.icon(
                    icon: const Icon(Icons.support_agent),
                    label: Text(t.mentorAskDirectGold),
                    onPressed: mentor.isAvailable ? _askMentor : null,
                  ),
          ],
          const SizedBox(height: 16),
          Text(t.mentorPortfolioTitle,
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          GridView.count(
            crossAxisCount: 3,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 8,
            crossAxisSpacing: 8,
            children: [
              for (final sid in mentor.portfolioSubmissionIds)
                ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.network(
                    ApiClient.instance.imageUrl(sid),
                    headers: ApiClient.instance.authHeaders,
                    fit: BoxFit.cover,
                    errorBuilder: (_, _, _) => const Icon(Icons.image),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Mentora destek (bağış) kartı.
///
/// Apple §3.2.1, kişi-kişiye hediyeye üç şartla izin veriyor ve bu widget
/// üçünü de korumak zorunda:
///  1. Tamamen isteğe bağlı — metin bunu açıkça söylüyor, hiçbir akış bunu
///     zorunlu kılmıyor ve geri bildirim almak için gerekmiyor.
///  2. Tutarın %100'ü mentora gidiyor — Artora kesinti almıyor, ödeme
///     uygulamadan geçmiyor.
///  3. Uygulamada HİÇBİR ŞEY açmıyor — destekçi rozeti, öncelik, sıralama
///     etkisi, "daha hızlı cevap" gibi bir karşılığı YOK. Buraya böyle bir
///     ödül eklemek doğrudan kural ihlalidir.
///
/// Ödeme uygulama içinde değil: link sistem tarayıcısında açılır
/// (LaunchMode.externalApplication — webview kullanmıyoruz).
class _DonationCard extends StatelessWidget {
  const _DonationCard({required this.url, required this.platform});

  final String url;
  final String platform;

  Future<void> _open(BuildContext context) async {
    final t = AppLocalizations.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(t.donationLeaveTitle),
        content: Text(t.donationLeaveBody(platform)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: Text(t.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(t.donationLeaveConfirm),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(t.errorUnexpected)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Card(
      margin: EdgeInsets.zero,
      color: scheme.surfaceContainerHighest,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Icon(Icons.volunteer_activism, size: 18, color: scheme.primary),
              const SizedBox(width: 8),
              Expanded(
                child: Text(t.donationTitle,
                    style: Theme.of(context).textTheme.titleSmall),
              ),
            ]),
            const SizedBox(height: 8),
            Text(t.donationBody, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 8),
            Text(
              t.donationOptionalNote,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: scheme.onSurfaceVariant,
                    fontStyle: FontStyle.italic,
                  ),
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerLeft,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.open_in_new, size: 18),
                label: Text(platform.isEmpty
                    ? t.donationButton
                    : '${t.donationButton} · $platform'),
                onPressed: () => _open(context),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
