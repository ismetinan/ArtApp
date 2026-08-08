import 'dart:async';

import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';

/// Asenkron analiz işinin takibi (Faz 2).
///
/// Eskiden analiz HTTP isteğinin içinde koşuyordu: uygulama ölürse sonuç
/// kullanıcıya hiç ulaşmıyordu (jeton harcanmış, çizim yalnız galeride).
/// Artık sunucu iş kimliğini hemen döndürüyor, iş arka planda koşuyor ve
/// istemci onu sorguluyor. Uygulama kapansa bile iş kimliği diskte durduğu
/// için açılışta sonuç bulunabiliyor.
class AnalysisWatcher {
  const AnalysisWatcher._();

  static const _kJobId = 'analysis_job_id';

  static Future<void> remember(int jobId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_kJobId, jobId);
  }

  static Future<void> forget() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kJobId);
  }

  static Future<int?> rememberedJobId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_kJobId);
  }

  /// İş bitene kadar sorgular. Tamamlandığında hatırlanan kimliği siler.
  ///
  /// Aralık kademeli: analiz tipik olarak 30-60 sn sürüyor, ilk saniyelerde
  /// sık sormanın anlamı yok ama bittiği anda göstermek istiyoruz.
  /// [onStatus] her sorgudan sonra çağrılır (arayüz durum yazısı için).
  static Future<AnalysisJobInfo> waitFor(
    int jobId, {
    void Function(AnalysisJobInfo)? onStatus,
    Duration timeout = const Duration(minutes: 4),
  }) async {
    final deadline = DateTime.now().add(timeout);
    var interval = const Duration(seconds: 2);
    while (true) {
      final job = await ApiClient.instance.getAnalysisJob(jobId);
      onStatus?.call(job);
      if (job.isFinished) {
        await forget();
        return job;
      }
      if (DateTime.now().isAfter(deadline)) {
        // Sunucu işi bırakmadı; kimliği DİSKTE BIRAKIYORUZ ki bir sonraki
        // açılışta kurtarma yine denesin. Zaman aşımı istemci tarafıdır.
        return job;
      }
      await Future.delayed(interval);
      if (interval < const Duration(seconds: 5)) {
        interval += const Duration(seconds: 1);
      }
    }
  }

  /// Açılışta/resume'da: yarım kalmış iş varsa sonucunu getirir.
  ///
  /// Önce diskteki kimliğe bakar; yoksa sunucudaki son işi sorar (uygulama
  /// verisi silinmiş ya da başka cihazdan bakılıyor olabilir). Gösterilecek
  /// bir sonuç yoksa null döner.
  static Future<AnalysisJobInfo?> recover() async {
    final jobId = await rememberedJobId();
    try {
      final job = jobId != null
          ? await ApiClient.instance.getAnalysisJob(jobId)
          : await ApiClient.instance.getLatestAnalysisJob();
      if (job == null) return null;
      if (job.isFinished) {
        await forget();
        // Diskte kimlik yoksa bu "son iş"tir; kullanıcı zaten görmüş olabilir,
        // o yüzden yalnız hatırlanan iş için sonuç gösterilir.
        return jobId == null ? null : job;
      }
      // Hâlâ koşuyor: kimliği koru, çağıran bekleme ekranını sürdürebilir.
      return job;
    } catch (_) {
      return null; // ağ yoksa kurtarma sessizce atlanır
    }
  }
}
