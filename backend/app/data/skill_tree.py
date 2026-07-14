"""Faz 1 statik yetenek ağacı seed verisi.

YouTube video ID'leri PLACEHOLDER — gerçek müfredat küratörlüğü kullanıcının işi
(CLAUDE.md §8). Yapı: 3 eksende ~10 düğüm, önkoşul zinciriyle.
"""

SEED_NODES = [
    # Temel kök düğüm
    dict(id="cizgi-temelleri", title="Çizgi Temelleri", skill_axis="cizgi_kalitesi",
         description="Isınma egzersizleri, çizgi kontrolü ve el rahatlığı.",
         youtube_video_id="PLACEHOLDER", xp_reward=40, prerequisites=[]),
    # Oran dalı
    dict(id="temel-oranlar", title="Temel Oranlar", skill_axis="oran",
         description="Basit nesnelerde ölçü alma ve karşılaştırma.",
         youtube_video_id="PLACEHOLDER", xp_reward=50, prerequisites=["cizgi-temelleri"]),
    dict(id="figur-oranlari", title="Figür Oranları", skill_axis="oran",
         description="İnsan figüründe baş boyu ölçüsü ve temel oranlar.",
         youtube_video_id="PLACEHOLDER", xp_reward=60, prerequisites=["temel-oranlar"]),
    # Anatomi dalı
    dict(id="jest-cizimi", title="Jest Çizimi (Gesture)", skill_axis="anatomi",
         description="30 saniyelik hızlı poz etütleriyle hareketi yakalama.",
         youtube_video_id="PLACEHOLDER", xp_reward=50, prerequisites=["cizgi-temelleri"]),
    dict(id="temel-anatomi", title="Temel Anatomi", skill_axis="anatomi",
         description="İskelet ve büyük kas gruplarının basitleştirilmiş formları.",
         youtube_video_id="PLACEHOLDER", xp_reward=70, prerequisites=["jest-cizimi", "figur-oranlari"]),
    # Perspektif dalı
    dict(id="tek-nokta-perspektif", title="Tek Noktalı Perspektif", skill_axis="perspektif",
         description="Ufuk çizgisi ve kaçış noktasıyla derinlik kurma.",
         youtube_video_id="PLACEHOLDER", xp_reward=50, prerequisites=["cizgi-temelleri"]),
    dict(id="iki-nokta-perspektif", title="İki Noktalı Perspektif", skill_axis="perspektif",
         description="Kutu formlarla mekân ve nesne kurulumu.",
         youtube_video_id="PLACEHOLDER", xp_reward=60, prerequisites=["tek-nokta-perspektif"]),
    # Işık-gölge dalı
    dict(id="isik-mantigi", title="Işığın Mantığı", skill_axis="isik_golge",
         description="Tek ışık kaynağıyla temel form gölgelendirme.",
         youtube_video_id="PLACEHOLDER", xp_reward=50, prerequisites=["temel-oranlar"]),
    dict(id="deger-calismasi", title="Değer (Value) Çalışması", skill_axis="isik_golge",
         description="Açık-koyu ilişkileriyle hacim ve odak yaratma.",
         youtube_video_id="PLACEHOLDER", xp_reward=60, prerequisites=["isik-mantigi"]),
    # Kompozisyon
    dict(id="temel-kompozisyon", title="Temel Kompozisyon", skill_axis="kompozisyon",
         description="Üçler kuralı, odak noktası ve görsel akış.",
         youtube_video_id="PLACEHOLDER", xp_reward=60,
         prerequisites=["iki-nokta-perspektif", "deger-calismasi"]),
]
