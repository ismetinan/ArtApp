import 'dart:developer' as dev;

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'api.dart';
import 'screens/mentor_panel.dart';
import 'screens/profile.dart';

/// Uygulama öndeyken gelen bildirimleri SnackBar olarak göstermek için
/// MaterialApp'e verilen global messenger anahtarı.
final GlobalKey<ScaffoldMessengerState> messengerKey =
    GlobalKey<ScaffoldMessengerState>();

/// Bildirim derin bağlantıları için MaterialApp'e verilen navigator anahtarı.
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

bool _initialMessageHandled = false;

/// Bildirime dokununca ilgili ekranı açar (data.route sunucudan gelir).
void _openRoute(RemoteMessage message) {
  final nav = navigatorKey.currentState;
  if (nav == null) return;
  switch (message.data['route']) {
    case 'mentor_panel':
      nav.push(MaterialPageRoute(builder: (_) => const MentorPanelScreen()));
    case 'my_requests':
      nav.push(MaterialPageRoute(builder: (_) => const MyRequestsScreen()));
    // 'profile' ve bilinmeyen rotalar: uygulamayı açmak yeterli
  }
}

bool _firebaseReady = false;
bool _listenersBound = false;

/// Firebase'i bir kez başlatır; yapılandırma yoksa false döner, asla fırlatmaz.
/// main() (Crashlytics için) ve initPush ortak kullanır.
Future<bool> ensureFirebase() async {
  if (_firebaseReady) return true;
  try {
    await Firebase.initializeApp();
    _firebaseReady = true;
  } catch (e) {
    dev.log('Firebase başlatılamadı: $e');
  }
  return _firebaseReady;
}

/// FCM kurulumu: izin iste → token al → backend'e kaydet → dinleyicileri bağla.
/// Oturum yoksa veya Firebase yapılandırması eksikse (google-services.json)
/// sessizce atlanır — push, ana akışı hiçbir koşulda bozmaz.
Future<void> initPush() async {
  if (ApiClient.instance.token == null) return;
  if (!await ensureFirebase()) return;
  try {
    if (!_listenersBound) {
      _listenersBound = true;

      // Uygulama öndeyken sistem bildirimi görünmez — SnackBar ile gösteririz
      FirebaseMessaging.onMessage.listen((message) {
        final n = message.notification;
        if (n == null) return;
        messengerKey.currentState?.showSnackBar(SnackBar(
          content: Text([n.title, n.body].whereType<String>().join('\n')),
          duration: const Duration(seconds: 5),
        ));
      });

      FirebaseMessaging.instance.onTokenRefresh.listen((token) {
        ApiClient.instance.registerDevice(token).catchError((_) {});
      });

      // Derin bağlantı: arka plandayken bildirime dokunuldu
      FirebaseMessaging.onMessageOpenedApp.listen(_openRoute);
    }

    // Derin bağlantı: uygulama bildirimle SOĞUK açıldıysa (bir kez işlenir)
    if (!_initialMessageHandled) {
      _initialMessageHandled = true;
      final initial = await FirebaseMessaging.instance.getInitialMessage();
      if (initial != null) _openRoute(initial);
    }

    await FirebaseMessaging.instance.requestPermission();
    final token = await FirebaseMessaging.instance.getToken();
    if (token != null) {
      await ApiClient.instance.registerDevice(token);
    }
  } catch (e) {
    // google-services.json yok / Play Services yok / ağ hatası — uygulama açılır
    dev.log('Push kurulumu atlandı: $e');
  }
}
