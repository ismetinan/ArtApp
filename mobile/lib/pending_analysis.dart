import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Yarım kalmış AI analizlerinin kurtarılması.
///
/// İki gerçek kayıp senaryosu var; ikisi de Android'in uygulamayı arka planda
/// öldürmesinden doğuyor (kamera/galeri ayrı bir activity, düşük bellekte
/// Artora sıklıkla kapatılıyor):
///
/// 1. **Seçici sırasında ölüm.** Kullanıcı "yükle"ye basar, galeri açılır,
///    Android Artora'yı öldürür. Kullanıcı fotoğrafı seçer, geri döner,
///    uygulama sıfırdan başlar — `pickImage`'in Future'ı asla tamamlanmaz ve
///    seçilen fotoğraf SESSİZCE kaybolur. Kullanıcı eski ekranda bulur kendini
///    ve "hiçbir şey olmadı" sanır. image_picker bunun için `retrieveLostData`
///    sunuyor; çağrılmazsa veri geri alınamaz.
///
/// 2. **Analiz sırasında ölüm.** İstek gönderildi, sunucu analizi tamamlayıp
///    KAYDETTİ (ölçüldü), ama istemci öldüğü için sonucu göremedi. Jeton
///    harcandı, kullanıcı elinde bir şey olmadığını sanıp tekrar yükleyebilir —
///    yani ikinci kez jeton harcar. Bayrak sayesinde açılışta sonucu bulup
///    gösteriyoruz.
///
/// Not: Bu bir yara bandı. Kalıcı çözüm analizi sunucuda asenkron işe çevirip
/// istemcinin iş kimliğiyle sorgulaması (bkz. yol haritası raporu).
class PendingAnalysis {
  const PendingAnalysis._();

  static const _kNodeId = 'pending_analysis_node';
  static const _kStage = 'pending_analysis_stage';

  /// `picking`: seçici açıldı, dosya henüz elimizde değil.
  /// `uploading`: dosya sunucuya gönderildi, sonuç bekleniyor.
  static const stagePicking = 'picking';
  static const stageUploading = 'uploading';

  /// Serbest analizde düğüm yok; bu sabit onun yerine geçer.
  static const freeAnalysisNode = '__free__';

  static Future<void> mark(String nodeId, String stage) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kNodeId, nodeId);
    await prefs.setString(_kStage, stage);
  }

  static Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kNodeId);
    await prefs.remove(_kStage);
  }

  static Future<({String nodeId, String stage})?> read() async {
    final prefs = await SharedPreferences.getInstance();
    final nodeId = prefs.getString(_kNodeId);
    final stage = prefs.getString(_kStage);
    if (nodeId == null || stage == null) return null;
    return (nodeId: nodeId, stage: stage);
  }

  /// Seçici sırasında öldüysek fotoğrafı geri alır (yalnız Android'de dolu
  /// döner; diğer platformlarda kayıp veri kavramı yok).
  static Future<XFile?> recoverLostImage() async {
    try {
      final lost = await ImagePicker().retrieveLostData();
      if (lost.isEmpty || lost.file == null) return null;
      return lost.file;
    } catch (_) {
      return null; // kurtarma başarısızsa akışı bozma
    }
  }
}
