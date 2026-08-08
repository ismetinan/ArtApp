import 'package:flutter/material.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';
import 'store.dart';

const _severityColors = {
  'dusuk': Color(0xFFF0C020),
  'orta': Color(0xFFF07020),
  'yuksek': Color(0xFFE02020),
};

/// Çizim + koordinatlı bulgu işaretleri — RedlineScreen ve mentor paneli
/// istek detayında ortak kullanılır.
class RedlineImage extends StatelessWidget {
  final ImageProvider image;
  final RedlineResult analysis;
  const RedlineImage({super.key, required this.image, required this.analysis});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) => Stack(
        fit: StackFit.expand,
        children: [
          Image(image: image, fit: BoxFit.contain),
          for (var i = 0; i < analysis.findings.length; i++)
            Positioned(
              left: analysis.findings[i].x * constraints.maxWidth - 14,
              top: analysis.findings[i].y * constraints.maxHeight - 14,
              child: _Marker(index: i + 1, finding: analysis.findings[i]),
            ),
        ],
      ),
    );
  }
}

/// AI redline sonucu: çizim + işaretler + yapıcı notlar. submissionId verilirse
/// ve mentor pazarı açıksa "Mentora sor — 1 jeton" aksiyonu görünür
/// (AI yeterli hissettirmezse insan mentor akışı, CLAUDE.md §2.4).
class RedlineScreen extends StatefulWidget {
  final ImageProvider image;
  final RedlineResult analysis;
  final int xpAwarded;
  final int? submissionId;

  const RedlineScreen({
    super.key,
    required this.image,
    required this.analysis,
    this.xpAwarded = 0,
    this.submissionId,
  });

  @override
  State<RedlineScreen> createState() => _RedlineScreenState();
}

class _RedlineScreenState extends State<RedlineScreen> {
  bool _requestBusy = false;
  bool _requestSent = false;

  Future<void> _askMentor() async {
    setState(() => _requestBusy = true);
    try {
      final result =
          await ApiClient.instance.requestMentor(widget.submissionId!);
      _requestSent = true;
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(AppLocalizations.of(context)
                .mentorAskSent(result.mentorName))));
      }
    } catch (e) {
      if (mounted) showErrorWithStoreAction(context, e);
    } finally {
      if (mounted) setState(() => _requestBusy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final analysis = widget.analysis;
    return Scaffold(
      appBar: AppBar(title: Text(t.aiAnalysisTitle)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (widget.xpAwarded > 0)
            Card(
              color: Theme.of(context).colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(children: [
                  const Icon(Icons.stars),
                  const SizedBox(width: 8),
                  Text(t.xpGained(widget.xpAwarded),
                      style: Theme.of(context).textTheme.titleMedium),
                ]),
              ),
            ),
          const SizedBox(height: 8),
          AspectRatio(
            aspectRatio: 3 / 4,
            child: RedlineImage(image: widget.image, analysis: analysis),
          ),
          const SizedBox(height: 16),
          Text(t.strengthsTitle,
              style: Theme.of(context).textTheme.titleMedium),
          for (final s in analysis.strengthsTr)
            ListTile(
              dense: true,
              leading: const Icon(Icons.thumb_up, color: Colors.green),
              title: Text(s),
            ),
          const SizedBox(height: 8),
          Text(t.findingsTitle,
              style: Theme.of(context).textTheme.titleMedium),
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
                subtitle:
                    Text(t.suggestionPrefix(analysis.findings[i].suggestionTr)),
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
          if (widget.submissionId != null &&
              ApiClient.instance.mentorMarketEnabled &&
              !_requestSent) ...[
            const SizedBox(height: 16),
            // Yeni ekonomide havuza sormak ücretsiz; bedelin yerini kotalar aldı
            JetonPaymentInfo(
              title: ApiClient.instance.jetonAiEconomy
                  ? t.mentorFreeTitle
                  : t.jetonPaymentTitle,
              body: ApiClient.instance.jetonAiEconomy
                  ? t.mentorFreeInfo(3)
                  : t.mentorPoolPaymentInfo,
            ),
            const SizedBox(height: 8),
            _requestBusy
                ? const Center(child: CircularProgressIndicator())
                : OutlinedButton.icon(
                    icon: const Icon(Icons.support_agent),
                    label: Text(ApiClient.instance.jetonAiEconomy
                        ? t.mentorAskFree
                        : t.mentorAsk),
                    onPressed: _askMentor,
                  ),
          ],
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
