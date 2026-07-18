import 'dart:developer' as dev;

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';

import 'api.dart';

/// Uygulama öndeyken gelen bildirimleri SnackBar olarak göstermek için
/// MaterialApp'e verilen global messenger anahtarı.
final GlobalKey<ScaffoldMessengerState> messengerKey =
    GlobalKey<ScaffoldMessengerState>();

bool _firebaseReady = false;

/// FCM kurulumu: izin iste → token al → backend'e kaydet → dinleyicileri bağla.
/// Oturum yoksa veya Firebase yapılandırması eksikse (google-services.json)
/// sessizce atlanır — push, ana akışı hiçbir koşulda bozmaz.
Future<void> initPush() async {
  if (ApiClient.instance.token == null) return;
  try {
    if (!_firebaseReady) {
      await Firebase.initializeApp();
      _firebaseReady = true;

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
