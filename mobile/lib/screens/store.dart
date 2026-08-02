import 'dart:async';

import 'package:flutter/material.dart';
import 'package:in_app_purchase/in_app_purchase.dart';

import '../api.dart';
import '../l10n/gen/app_localizations.dart';

/// Jeton ürün kimlikleri — Play Console + backend kataloğuyla birebir aynı
/// (backend/app/services/billing.py JETON_PRODUCTS).
const jetonProducts = {'jeton_5': 5, 'jeton_15': 15, 'jeton_40': 40};
const subscriptionProduct = 'premium_monthly';

/// Altın jetonun görsel kimliği — profil çipi, mağaza ve mentor akışlarında aynı.
const goldJetonColor = Color(0xFFD4AF37);

/// Ücretsiz vs altın jeton farkını açıklayan bilgi kartı. Mentor isteği
/// akışlarında (havuz/seçmeli) ve mağazada ödemenin nasıl işlediğini anlatır.
class JetonPaymentInfo extends StatelessWidget {
  final String body;
  final String? title;
  const JetonPaymentInfo({super.key, required this.body, this.title});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.surfaceContainerHighest,
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, size: 20, color: scheme.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (title != null) ...[
                    Text(title!,
                        style: Theme.of(context)
                            .textTheme
                            .labelLarge
                            ?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                  ],
                  Text(body, style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Hata SnackBar'ı: jeton yetersiz (402) ve mağaza açıksa "Jeton Al" aksiyonu
/// ekler; diğer hatalarda düz mesaj gösterir.
void showErrorWithStoreAction(BuildContext context, Object e) {
  final messenger = ScaffoldMessenger.of(context);
  final isJetonError = e is ApiException && e.statusCode == 402;
  messenger.showSnackBar(SnackBar(
    content: Text(friendlyError(context, e)),
    action: (isJetonError && ApiClient.instance.billingEnabled)
        ? SnackBarAction(
            label: AppLocalizations.of(context).storeBuyJetons,
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const StoreScreen()),
            ),
          )
        : null,
  ));
}

/// Jeton Mağazası: paketler + Premium abonelik. Satın alma Play'de biter,
/// hak backend doğrulamasıyla verilir; 200 gelmeden completePurchase yok.
class StoreScreen extends StatefulWidget {
  final bool isPremium;
  final String? premiumUntil;
  const StoreScreen({super.key, this.isPremium = false, this.premiumUntil});

  @override
  State<StoreScreen> createState() => _StoreScreenState();
}

class _StoreScreenState extends State<StoreScreen> {
  final _iap = InAppPurchase.instance;
  StreamSubscription<List<PurchaseDetails>>? _sub;
  Map<String, ProductDetails> _products = {};
  bool _loading = true;
  bool _storeAvailable = false;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _sub = _iap.purchaseStream.listen(_onPurchases, onError: (Object e) {
      if (mounted) setState(() => _busy = false);
    });
    _load();
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      _storeAvailable = await _iap.isAvailable();
      if (_storeAvailable) {
        final ids = {...jetonProducts.keys, subscriptionProduct};
        final resp = await _iap.queryProductDetails(ids);
        _products = {for (final p in resp.productDetails) p.id: p};
      }
    } catch (_) {
      _storeAvailable = false;
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _buy(String productId) async {
    final details = _products[productId];
    if (details == null || _busy) return;
    setState(() => _busy = true);
    final param = PurchaseParam(productDetails: details);
    try {
      if (jetonProducts.containsKey(productId)) {
        // autoConsume kapalı: önce backend doğrular, sonra completePurchase
        await _iap.buyConsumable(purchaseParam: param, autoConsume: false);
      } else {
        await _iap.buyNonConsumable(purchaseParam: param);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _busy = false);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
      }
    }
  }

  Future<void> _onPurchases(List<PurchaseDetails> purchases) async {
    for (final p in purchases) {
      switch (p.status) {
        case PurchaseStatus.purchased:
        case PurchaseStatus.restored:
          await _verify(p);
        case PurchaseStatus.error:
        case PurchaseStatus.canceled:
          if (mounted) setState(() => _busy = false);
          if (p.pendingCompletePurchase) await _iap.completePurchase(p);
        case PurchaseStatus.pending:
          break; // Play tamamlanınca stream yeniden tetiklenir
      }
    }
  }

  Future<void> _verify(PurchaseDetails p) async {
    try {
      final status = await ApiClient.instance.verifyPurchase(
        p.productID,
        p.verificationData.serverVerificationData,
      );
      // Hak sunucuda verildi — Play tarafını kapat (consumable'da consume eder)
      if (p.pendingCompletePurchase) await _iap.completePurchase(p);
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(AppLocalizations.of(context)
              .storeSuccess((status['gold_jeton_balance'] ?? 0) as int))));
      Navigator.of(context).pop(true); // profil yenilensin
    } catch (e) {
      // Doğrulama başarısız: completePurchase ÇAĞIRMA — restore ile tekrar denenir
      if (!mounted) return;
      setState(() => _busy = false);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(friendlyError(context, e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(t.storeTitle)),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : !_storeAvailable
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Text(t.storeUnavailable, textAlign: TextAlign.center),
                  ),
                )
              : ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    JetonPaymentInfo(body: t.storeGoldExplainer),
                    const SizedBox(height: 16),
                    _PremiumCard(
                      product: _products[subscriptionProduct],
                      isPremium: widget.isPremium,
                      premiumUntil: widget.premiumUntil,
                      busy: _busy,
                      onSubscribe: () => _buy(subscriptionProduct),
                    ),
                    const SizedBox(height: 24),
                    Text(t.storeJetonSection,
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    for (final entry in jetonProducts.entries)
                      _JetonCard(
                        count: entry.value,
                        product: _products[entry.key],
                        busy: _busy,
                        onBuy: () => _buy(entry.key),
                      ),
                    const SizedBox(height: 16),
                    TextButton(
                      onPressed:
                          _busy ? null : () => _iap.restorePurchases(),
                      child: Text(t.storeRestore),
                    ),
                  ],
                ),
    );
  }
}

class _PremiumCard extends StatelessWidget {
  final ProductDetails? product;
  final bool isPremium;
  final String? premiumUntil;
  final bool busy;
  final VoidCallback onSubscribe;
  const _PremiumCard({
    required this.product,
    required this.isPremium,
    required this.premiumUntil,
    required this.busy,
    required this.onSubscribe,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.workspace_premium, color: scheme.primary),
                const SizedBox(width: 8),
                Text(t.storePremiumTitle,
                    style: Theme.of(context).textTheme.titleLarge),
              ],
            ),
            const SizedBox(height: 12),
            for (final perk in [
              t.storePremiumPerk1(10),
              t.storePremiumPerk2,
              t.storePremiumPerk3,
            ])
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.check, size: 18),
                    const SizedBox(width: 8),
                    Expanded(child: Text(perk)),
                  ],
                ),
              ),
            const SizedBox(height: 12),
            if (isPremium)
              Chip(
                avatar: const Icon(Icons.verified, size: 18),
                label: Text(t.storePremiumActive(
                    premiumUntil?.split('T').first ?? '')),
              )
            else
              FilledButton(
                onPressed: (product == null || busy) ? null : onSubscribe,
                child: Text(product == null
                    ? t.storeSubscribe
                    : '${t.storeSubscribe} — ${product!.price}'),
              ),
          ],
        ),
      ),
    );
  }
}

class _JetonCard extends StatelessWidget {
  final int count;
  final ProductDetails? product;
  final bool busy;
  final VoidCallback onBuy;
  const _JetonCard({
    required this.count,
    required this.product,
    required this.busy,
    required this.onBuy,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context);
    return Card(
      child: ListTile(
        leading: const Icon(Icons.paid, color: goldJetonColor),
        title: Text(t.storeJetonPack(count)),
        subtitle: product == null ? null : Text(product!.price),
        trailing: FilledButton.tonal(
          onPressed: (product == null || busy) ? null : onBuy,
          child: Text(t.storeBuy),
        ),
      ),
    );
  }
}
