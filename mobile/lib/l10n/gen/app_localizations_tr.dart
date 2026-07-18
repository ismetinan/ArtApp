// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Turkish (`tr`).
class AppLocalizationsTr extends AppLocalizations {
  AppLocalizationsTr([String locale = 'tr']) : super(locale);

  @override
  String get tabMentors => 'Mentorlar';

  @override
  String get tabLessons => 'Dersler';

  @override
  String get tabProfile => 'Profil';

  @override
  String get welcomeTagline => 'Çizimde gelişim yolculuğun burada başlıyor.';

  @override
  String get continueAsGuest => 'Misafir Olarak Devam Et';

  @override
  String get continueWithGoogle => 'Google ile Devam Et';

  @override
  String get signIn => 'Giriş Yap';

  @override
  String get signUp => 'Kayıt Ol';

  @override
  String get createAccount => 'Hesap Oluştur';

  @override
  String get guestDefaultName => 'Misafir Çizer';

  @override
  String get artistDefaultName => 'Çizer';

  @override
  String get errorNetwork =>
      'Sunucuya ulaşılamadı. İnternet bağlantını ve backend\'i kontrol et.';

  @override
  String get errorUnexpected => 'Beklenmeyen bir sorun oluştu.';

  @override
  String get upgradeNote =>
      'İlerlemen aynen korunacak — sadece e-posta ve şifre ekliyoruz ki hesabın güvende olsun.';

  @override
  String get labelDisplayName => 'Görünen ad';

  @override
  String get labelEmail => 'E-posta';

  @override
  String get labelPassword => 'Şifre';

  @override
  String get validEmail => 'Geçerli bir e-posta gir';

  @override
  String get validPasswordMin => 'En az 8 karakter';

  @override
  String get orDivider => 'veya';

  @override
  String get pickTitle => 'Son 3 Çizimini Yükle';

  @override
  String get pickIntro =>
      'Seviyeni belirlemek için son yaptığın 3 çizimi seç. Mükemmel olmaları gerekmiyor — olduğun yerden başlıyoruz.';

  @override
  String pickContinue(int count) {
    return 'Devam Et ($count/3)';
  }

  @override
  String get pickCamera => 'Kamera ile çek';

  @override
  String get pickGallery => 'Cihazdan seç';

  @override
  String get analyzingTitle => 'Resimlerin inceleniyor...';

  @override
  String get analyzingSubtitle => 'Bu birkaç saniye sürebilir.';

  @override
  String analyzeRetry(String error) {
    return '$error Birazdan tekrar denenecek.';
  }

  @override
  String get resultTitle => 'Değerlendirme Sonucu';

  @override
  String levelHeading(int level) {
    return '$level. Seviye';
  }

  @override
  String scoreDetermined(int score) {
    return '$score/100 — belirlendi';
  }

  @override
  String get goToTree => 'Yetenek Ağacına Git';

  @override
  String get mentorsComingTitle => 'Mentor pazarı çok yakında!';

  @override
  String get mentorsComingBody =>
      'Şimdilik her ödevine anında ücretsiz AI analizi alabilirsin. Gerçek mentorlar bir sonraki sürümde burada olacak.';

  @override
  String treeLoadError(String error) {
    return 'Ağaç yüklenemedi: $error';
  }

  @override
  String get lockedSnack =>
      'Bu ders için önce önceki dersleri tamamlaman gerekiyor.';

  @override
  String nodeMeta(String axis, int xp) {
    return '$axis • $xp XP';
  }

  @override
  String get videoSoon => 'Video yakında';

  @override
  String get videoSoonBody => 'Bu dersin içeriği henüz eklenmedi.';

  @override
  String get resourceKindPlaylist => 'Oynatma listesi';

  @override
  String get resourceKindVideo => 'Video';

  @override
  String resourceMeta(String author, String kind) {
    return '$author • $kind';
  }

  @override
  String get uploadHomework => 'Ödevini yükle';

  @override
  String get uploadHint =>
      'Videoyu izledikten sonra çalışmanı yükle; saniyeler içinde yapıcı bir redline analizi alacaksın.';

  @override
  String get submitFromDevice => 'Cihazdan Seç ve Gönder';

  @override
  String get submitFromCamera => 'Kamera ile Çek ve Gönder';

  @override
  String get aiAnalysisTitle => 'AI Analizi';

  @override
  String xpGained(int xp) {
    return '+$xp XP kazandın!';
  }

  @override
  String get strengthsTitle => 'Güçlü yönlerin';

  @override
  String get findingsTitle => 'Gelişim noktaları';

  @override
  String suggestionPrefix(String text) {
    return 'Öneri: $text';
  }

  @override
  String profileLoadError(String error) {
    return 'Profil yüklenemedi: $error';
  }

  @override
  String get createAccountCard => 'Hesap oluştur';

  @override
  String get createAccountCardBody =>
      'İlerlemen cihaz silinse bile güvende kalsın.';

  @override
  String levelBadge(int level, int xp) {
    return '$level. Seviye • $xp XP';
  }

  @override
  String get abilityChartTitle => 'Ability Chart';

  @override
  String get abilityChartHint =>
      'Bir eksene dokunarak ilgili derslere gidebilirsin.';

  @override
  String get chartEmpty =>
      'Seviye belirleme tamamlanınca chart burada görünecek.';

  @override
  String scoreOutOf(int score) {
    return '$score/100';
  }

  @override
  String get journeyTitle => 'Gelişim Macerası';

  @override
  String get journeyHint => 'Yüklediğin ödevler ve AI notların, kronolojik.';

  @override
  String get journeyEmpty =>
      'İlk ödevini yüklediğinde maceran burada başlayacak!';

  @override
  String get homeworkFallback => 'Ödev';

  @override
  String get privacyKeyHint =>
      'Anahtar: açık = herkese görünür, kapalı = sadece sen (varsayılan).';

  @override
  String get languageTitle => 'Dil / Language';

  @override
  String get languageTurkish => 'Türkçe';

  @override
  String get languageEnglish => 'English';

  @override
  String get deleteAccount => 'Hesabı Sil';

  @override
  String get deleteAccountBody => 'Hesabın ve tüm çizimlerin kalıcı silinir.';

  @override
  String get deleteConfirmTitle => 'Hesabı sil?';

  @override
  String get deleteConfirmBody =>
      'Hesabın, ilerlemen ve yüklediğin tüm çizimler kalıcı olarak silinecek. Bu işlem geri alınamaz.';

  @override
  String get cancel => 'Vazgeç';

  @override
  String get continueButton => 'Devam Et';

  @override
  String get deleteConfirm2Title => 'Emin misin?';

  @override
  String get deleteConfirm2Body => 'Son onay: tüm verilerin şimdi silinecek.';

  @override
  String get deleteFinalButton => 'Hesabımı Kalıcı Olarak Sil';

  @override
  String get axisAnatomi => 'Anatomi';

  @override
  String get axisPerspektif => 'Perspektif';

  @override
  String get axisIsikGolge => 'Işık-Gölge';

  @override
  String get axisOran => 'Oran';

  @override
  String get axisCizgiKalitesi => 'Çizgi Kalitesi';

  @override
  String get axisKompozisyon => 'Kompozisyon';

  @override
  String get axisRenk => 'Renk';
}
