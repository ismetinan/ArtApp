"""Faz 1 statik yetenek ağacı seed verisi.

Müfredat kaynağı: art_sources.md (kullanıcının derlediği YouTube video/playlist'leri;
başlıklar oEmbed ile doğrulandı, düğüm eşlemesi orada belgelendi). Her düğümün
`resources` listesi ders içeriğidir; `youtube_video_id` geriye dönük uyumluluk için
ilk tekil videoyu taşır (yalnız playlist varsa boş).

Yapı: 7 eksende 16 düğüm, önkoşul zinciriyle. Uygulama açılışında upsert edilir —
buradaki değişiklikler yeniden başlatmada veritabanına yansır.
"""


def _video(youtube_id: str, title: str, author: str) -> dict:
    return dict(kind="video", youtube_id=youtube_id, title=title, author=author)


def _playlist(youtube_id: str, title: str, author: str) -> dict:
    return dict(kind="playlist", youtube_id=youtube_id, title=title, author=author)


SEED_NODES = [
    # Kök düğüm
    dict(id="cizgi-temelleri", title="Çizgi Temelleri", skill_axis="cizgi_kalitesi",
         description="Isınma egzersizleri, çizgi kontrolü ve el rahatlığı; sanat "
                     "temellerine doğru sırayla genel bakış.",
         youtube_video_id="", xp_reward=40, prerequisites=[],
         resources=[
             _playlist("PLxLnscStGPB8cra3LkxHBSXEIhw2D2Q5i",
                       "Art Fundamentals! The correct order.", "Braydon G."),
         ]),
    # Perspektif dalı
    dict(id="sekil-ve-form", title="Şekil ve Form", skill_axis="perspektif",
         description="2B şekilden 3B forma geçiş: kutu, silindir ve küreyle düşünme.",
         youtube_video_id="", xp_reward=50, prerequisites=["cizgi-temelleri"],
         resources=[
             _playlist("PLDHJ4RxK-8Tgt-AmgLSdkgdhjL_RS5wrE",
                       "Art fundamentals #1: Shapes and forms", "Tamistrash Rodriguez"),
         ]),
    dict(id="tek-nokta-perspektif", title="Tek Noktalı Perspektif", skill_axis="perspektif",
         description="Ufuk çizgisi ve kaçış noktasıyla derinlik kurma.",
         youtube_video_id="", xp_reward=50, prerequisites=["sekil-ve-form"],
         resources=[
             _playlist("PLtG4P3lq8RHFSW-SgbBpo3k-xq9H_tdE6",
                       "Learning Perspective", "Proko"),
         ]),
    dict(id="iki-nokta-perspektif", title="İki Noktalı Perspektif", skill_axis="perspektif",
         description="Kutu formlarla mekân ve nesne kurulumu (Learning Perspective "
                     "serisinin devamı).",
         youtube_video_id="", xp_reward=60, prerequisites=["tek-nokta-perspektif"],
         resources=[
             _playlist("PLtG4P3lq8RHFSW-SgbBpo3k-xq9H_tdE6",
                       "Learning Perspective (devamı)", "Proko"),
         ]),
    # Oran dalı
    dict(id="temel-oranlar", title="Temel Oranlar", skill_axis="oran",
         description="Basit nesnelerde ölçü alma ve karşılaştırma.",
         youtube_video_id="", xp_reward=50, prerequisites=["cizgi-temelleri"],
         resources=[]),  # kaynak açık — art_sources.md'ye eklenince buraya girer
    dict(id="figur-oranlari", title="Figür Oranları", skill_axis="oran",
         description="İnsan figüründe baş boyu ölçüsü ve akademik figür etütleri.",
         youtube_video_id="jF0JPyxQ_3Y", xp_reward=60, prerequisites=["temel-oranlar"],
         resources=[
             _video("jF0JPyxQ_3Y",
                    "1H ACADEMY LESSON for STUDENT has no MONEY", "Mmmmonexx"),
         ]),
    dict(id="kafa-oranlari", title="Kafa Oranları (Loomis)", skill_axis="oran",
         description="Loomis metoduyla her açıdan kafa kurulumu.",
         youtube_video_id="wAOldLWIDSM", xp_reward=60, prerequisites=["temel-oranlar"],
         resources=[
             _video("wAOldLWIDSM",
                    "Quickly Draw Heads with the Loomis Method - Part 1", "Proko"),
             _video("A6KMT4Potss",
                    "How to draw heads with Loomis Method", "Draw like a Sir"),
         ]),
    # Anatomi dalı
    dict(id="jest-cizimi", title="Jest Çizimi (Gesture)", skill_axis="anatomi",
         description="Hızlı poz etütleriyle hareketi ve karakteri yakalama.",
         youtube_video_id="xGhYfLQWbp0", xp_reward=50, prerequisites=["cizgi-temelleri"],
         resources=[
             _video("xGhYfLQWbp0",
                    "ELEMENTS OF CHARACTER: Gesture, Forms, and Animation",
                    "moderndayjames"),
         ]),
    dict(id="temel-anatomi", title="Temel Anatomi", skill_axis="anatomi",
         description="İskelet ve büyük kas gruplarının basitleştirilmiş formları.",
         youtube_video_id="", xp_reward=70,
         prerequisites=["jest-cizimi", "figur-oranlari"],
         resources=[
             _playlist("PLg3tq-SuqiTlyL1pZDwNxSnCTGBZOiHvn",
                       "PROKO ANATOMY TUTORIALS", "Proko (derleme)"),
         ]),
    dict(id="portre", title="Portre Çizimi", skill_axis="anatomi",
         description="Kafa kurulumundan yüz hatlarına: portre temelleri ve uzun etütler.",
         youtube_video_id="onSVS3AsQB4", xp_reward=80,
         prerequisites=["kafa-oranlari", "temel-anatomi"],
         resources=[
             _playlist("PLR2KBLDDnZz0pHBiiyrqlOB3FU-W5XX1k",
                       "Proko Portrait Drawing Fundamentals", "Proko (derleme)"),
             _video("onSVS3AsQB4", "5H CLASS", "Mmmmonexx"),
         ]),
    # Işık-gölge dalı
    dict(id="isik-mantigi", title="Işığın Mantığı", skill_axis="isik_golge",
         description="Tek ışık kaynağıyla temel form gölgelendirme ve değer kavramı.",
         youtube_video_id="MyrySvbuhsk", xp_reward=50, prerequisites=["temel-oranlar"],
         resources=[
             _video("MyrySvbuhsk",
                    "Go From Flat to Realistic Shading! Here's How", "Proko"),
             _video("fw5kamqbWnk",
                    "All About Value in Art: Light and Dark", "Mr. New's Art Class"),
         ]),
    dict(id="deger-calismasi", title="Değer (Value) Çalışması", skill_axis="isik_golge",
         description="Açık-koyu ilişkileriyle hacim ve odak yaratma; değer skalaları.",
         youtube_video_id="qNawqTqUrP0", xp_reward=60, prerequisites=["isik-mantigi"],
         resources=[
             _video("qNawqTqUrP0",
                    "Understanding Value and Drawing Value Scales",
                    "Mr. New's Art Class"),
             _video("BTYGWfiZnMA",
                    "Essential Values for Painting, Lighting and Design", "Marco Bucci"),
         ]),
    # Kompozisyon dalı
    dict(id="temel-kompozisyon", title="Temel Kompozisyon", skill_axis="kompozisyon",
         description="Odak noktası, görsel akış ve kompozisyonun temel soruları.",
         youtube_video_id="sopLk4Czp6M", xp_reward=60,
         prerequisites=["iki-nokta-perspektif", "deger-calismasi"],
         resources=[
             _video("sopLk4Czp6M",
                    "What makes a great composition?", "Ian Roberts"),
             _video("VwUZ3PivD6I", "Composition in Art Explained", "Art with Flo"),
         ]),
    dict(id="ileri-kompozisyon", title="İleri Kompozisyon", skill_axis="kompozisyon",
         description="Kural ve püf noktalarıyla kompozisyonu bilinçli tasarlama.",
         youtube_video_id="vsW_Ams5RSk", xp_reward=70,
         prerequisites=["temel-kompozisyon"],
         resources=[
             _video("vsW_Ams5RSk",
                    "COMPOSITION - 3 RULES I Wish I Knew When I Started Painting",
                    "Florent Farges"),
             _video("LITy81Feo4c",
                    "5 AMAZING Composition Tricks that Always Work", "Florent Farges"),
             _video("JuEkb6FNptE",
                    "My Top 10 Composition Tips for artists", "Tyler Edlin"),
         ]),
    # Renk dalı (7. eksen)
    dict(id="renk-temelleri", title="Renk Temelleri", skill_axis="renk",
         description="Değerden renge geçiş: ton, doygunluk ve renk sıcaklığı.",
         youtube_video_id="", xp_reward=60, prerequisites=["deger-calismasi"],
         resources=[
             _playlist("PL002hNYqg1VjoRaboVhLbbCPR_0i2xUxV",
                       "Color Marco Bucci", "Marco Bucci (derleme)"),
         ]),
    dict(id="boyama", title="Boyama", skill_axis="renk",
         description="Işık, renk ve kompozisyonu boyamada birleştirme; kısa pratik "
                     "seriler ve tam demolar.",
         youtube_video_id="", xp_reward=80, prerequisites=["renk-temelleri"],
         resources=[
             _playlist("PLLmXZMqb_9sbNLM83NrM005vRQHw1yTKn",
                       "10 Minutes to Better Painting Series", "Marco Bucci"),
             _playlist("PLLmXZMqb_9sZbJOiJeq17nScRV0uo6ZQe",
                       "Painting Tutorials / Demos", "Marco Bucci"),
         ]),
]
