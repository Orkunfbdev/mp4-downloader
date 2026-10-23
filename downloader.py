from __future__ import annotations

import os
import sys
import time
import re
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Windows UTF-8 / Türkçe karakter desteği ve Düşük Sistem Optimizasyonu
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    try:
        import ctypes
        # BELOW_NORMAL_PRIORITY_CLASS (0x00004000)
        # En eski/zayıf bilgisayarlarda bile Windows arayüzünün, farenin veya tarayıcının takılmasını önler
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00004000)
    except Exception:
        pass

# Gerekli kütüphaneleri kontrol et
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, FileSizeColumn, SpinnerColumn
    from rich.text import Text
except ImportError:
    print("\n[!] Gerekli kütüphaneler eksik. Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.\n")
    sys.exit(1)

console = Console(force_terminal=True, highlight=False)

# Dizinler
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

DOWNLOAD_DIR = Path.home() / "Desktop"
if not DOWNLOAD_DIR.exists():
    DOWNLOAD_DIR = Path.home() / "Masaüstü"
DOWNLOAD_DIR.mkdir(exist_ok=True)

TEMP_DIR = Path(os.environ.get('TEMP', str(DOWNLOAD_DIR))) / "mp4_downloader_temp"
TEMP_DIR.mkdir(exist_ok=True)

# FFmpeg yolunu belirle ve arkaplanda önbellekle
_CACHED_FFMPEG_PATH = None

def _ensure_ffmpeg_in_path(ffmpeg_file: str):
    """FFmpeg'in bulunduğu klasörü PATH ortam değişkenine ekler (yt-dlp kısmi kesme için zorunlu)."""
    try:
        p = str(Path(ffmpeg_file).parent.resolve())
        curr_path = os.environ.get("PATH", "")
        if p.lower() not in curr_path.lower():
            os.environ["PATH"] = p + os.pathsep + curr_path
    except Exception:
        pass

def _resolve_ffmpeg():
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH is not None:
        return
    import shutil
    w = shutil.which("ffmpeg")
    if w:
        _CACHED_FFMPEG_PATH = w
        _ensure_ffmpeg_in_path(w)
        return
    for p in [BASE_DIR / "ffmpeg.exe", Path.cwd() / "ffmpeg.exe", TEMP_DIR / "ffmpeg.exe"]:
        if p.exists():
            _CACHED_FFMPEG_PATH = str(p)
            _ensure_ffmpeg_in_path(str(p))
            return
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            exe_dir = Path(ffmpeg_exe).parent
            target_alias = exe_dir / "ffmpeg.exe"
            if not target_alias.exists():
                try:
                    shutil.copyfile(ffmpeg_exe, target_alias)
                except Exception:
                    temp_alias = TEMP_DIR / "ffmpeg.exe"
                    try:
                        shutil.copyfile(ffmpeg_exe, temp_alias)
                        target_alias = temp_alias
                    except Exception:
                        pass
            chosen = str(target_alias) if target_alias.exists() else ffmpeg_exe
            _CACHED_FFMPEG_PATH = chosen
            _ensure_ffmpeg_in_path(chosen)
            return
    except Exception:
        pass
    _CACHED_FFMPEG_PATH = ""

def get_ffmpeg_path():
    if _CACHED_FFMPEG_PATH is None:
        _resolve_ffmpeg()
    return _CACHED_FFMPEG_PATH if _CACHED_FFMPEG_PATH else None

def start_background_ffmpeg_check():
    t = threading.Thread(target=_resolve_ffmpeg, daemon=True)
    t.start()

def detect_platform(url: str) -> tuple[str, str]:
    """Linkten platformu ve uygun renk bilgisini döner."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube", "red"
    elif "tiktok.com" in url_lower:
        return "TikTok", "magenta"
    elif "instagram.com" in url_lower or "instagr.am" in url_lower:
        return "Instagram", "bright_magenta"
    elif "twitter.com" in url_lower or "x.com" in url_lower or "t.co" in url_lower:
        return "Twitter / X", "cyan"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower or "fb.com" in url_lower:
        return "Facebook", "blue"
    elif "reddit.com" in url_lower:
        return "Reddit", "bright_red"
    elif "twitch.tv" in url_lower:
        return "Twitch", "purple"
    elif "pinterest.com" in url_lower or "pin.it" in url_lower:
        return "Pinterest", "red"
    else:
        return "Web / Diğer", "green"

def format_duration(seconds):
    """Saniyeyi kullanıcı dostu Saat:Dakika:Saniye biçimine çevirir."""
    if seconds is None:
        return "Bilinmiyor"
    if seconds == float('inf'):
        return "Sonuna Kadar"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def format_duration_compact(seconds):
    """Dosya isimlerine uygun iki nokta (:) içermeyen süre etiketi döner."""
    if seconds is None or seconds == float('inf'):
        return "Son"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours:02d}.{mins:02d}.{secs:02d}"
    return f"{mins:02d}.{secs:02d}"

def parse_time_component(s: str, default_unit: str = 's') -> float:
    """Zaman bileşenini (01:20:00, 15:30, 2saat, 2h, 45dk vb.) saniyeye çevirir."""
    s = s.strip().lower()
    if not s or s in ['bas', 'baslangic', 'start', '0', '00', '00:00', '00:00:00']:
        return 0.0
    if s in ['son', 'bitis', 'end', 'inf', 'infinity']:
        return float('inf')

    # Birim eklerini kontrol et
    if s.endswith(('saat', 'h')):
        num = float(re.sub(r'[^\d.]', '', s) or 0)
        return num * 3600
    if s.endswith(('dk', 'dakika', 'min', 'm')):
        num = float(re.sub(r'[^\d.]', '', s) or 0)
        return num * 60
    if s.endswith(('sn', 'saniye', 'sec', 's')):
        num = float(re.sub(r'[^\d.]', '', s) or 0)
        return num

    parts = s.split(':')
    if len(parts) == 3:  # SS:DD:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:  # DD:SS
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 1:
        val = float(parts[0])
        if default_unit == 'h':
            return val * 3600
        elif default_unit == 'm':
            return val * 60
        return val
    return 0.0

def parse_time_range(raw_str: str, total_duration: float = None) -> tuple[float, float] | None:
    """Kullanıcının girdiği zaman aralığını (01:00:00-02:00:00, 2-3, 10:00-20:00 vb.) saniye çifti olarak çözer."""
    if not raw_str or not raw_str.strip():
        return None
    raw = raw_str.strip()
    raw = re.sub(r'\s+ile\s+', '-', raw, flags=re.I)
    raw = re.sub(r'\s+-\s+', '-', raw)
    raw = re.sub(r'\s+to\s+', '-', raw, flags=re.I)

    if '-' in raw:
        parts = raw.split('-', 1)
        start_part, end_part = parts[0], parts[1]
    else:
        parts = raw.split()
        if len(parts) == 2:
            start_part, end_part = parts[0], parts[1]
        else:
            return None

    def is_simple_num(x):
        try:
            return True, float(x.strip())
        except Exception:
            return False, 0.0

    s_is_num, s_val = is_simple_num(start_part)
    e_is_num, e_val = is_simple_num(end_part)

    default_unit = 's'
    # Video 1 saatten uzunsa ve kullanıcı sade rakam girdiyse (Örn: '2-3' veya '2 ile 3') saat olarak yorumla
    if s_is_num and e_is_num:
        if total_duration and total_duration >= 3600:
            if s_val <= 48 and e_val <= 48:
                default_unit = 'h'
        elif not total_duration and s_val <= 12 and e_val <= 12:
            default_unit = 'h'

    start_sec = parse_time_component(start_part, default_unit=default_unit)
    end_sec = parse_time_component(end_part, default_unit=default_unit)

    if total_duration and end_sec == float('inf'):
        end_sec = float(total_duration)

    if start_sec >= end_sec:
        return None

    return start_sec, end_sec

def open_download_folder():
    """Masaüstü klasörünü Windows Gezgini'nde açar."""
    try:
        os.startfile(str(DOWNLOAD_DIR))
        console.print(f"[bold green]✓ Masaüstü açıldı:[/bold green] [cyan]{DOWNLOAD_DIR}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Klasör açılamadı: {e}[/red]\n")

def _find_current_download_part(directories, started_at: float):
    """Return the newest partial file created or updated for this download."""
    latest_path = None
    latest_mtime = started_at
    for directory in directories:
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if not entry.name.endswith(('.part', '.ytdl')) or not entry.is_file():
                        continue
                    try:
                        mtime = entry.stat().st_mtime
                    except OSError:
                        continue
                    if mtime >= started_at and mtime > latest_mtime:
                        latest_path = Path(entry.path)
                        latest_mtime = mtime
        except OSError:
            continue
    return latest_path

def _format_download_rate(speed_mb: float, idle_seconds: float) -> str:
    if idle_seconds >= 3:
        return f"Veri bekleniyor ({int(idle_seconds)} sn)"
    if speed_mb > 0:
        return f"{speed_mb:.1f} MB/s"
    return "Bağlanıyor..."

def display_banner():
    """Modern, ultra hafif ve hiçbir sistemde kasma/taşma yapmayan şık başlık."""
    grid = Table(show_header=False, box=None, padding=(0, 0))
    grid.add_column()
    grid.add_row("[bold cyan]🎬 ORKUNFB[/bold cyan] [bold white]• MP4 İNDİRİCİ[/bold white] [bold green][0 CPU • Ultra Hızlı][/bold green]")
    grid.add_row("[dim cyan]──────────────────────────────────────────────────────────────────[/dim cyan]")
    grid.add_row("[bold white]📺 Platformlar:[/bold white] [cyan]YouTube[/cyan] • [magenta]Twitch[/magenta] • [white]TikTok[/white] • [cyan]X[/cyan] • [magenta]Instagram[/magenta] • [yellow]M3U8[/yellow]")
    grid.add_row("[bold white]✂️ Kesit İndir:[/bold white] [yellow]Zaman aralığı belirtebilirsiniz[/yellow] [dim]('25dk 48dk', '2-3')[/dim]")
    grid.add_row("[bold white]⚡ Donanım Dostu:[/bold white] [green]Sıfır CPU / Stream Copy[/green] • [cyan]En Yüksek Kalite[/cyan]")
    grid.add_row("[dim cyan]──────────────────────────────────────────────────────────────────[/dim cyan]")
    grid.add_row("[bold yellow]💡 Dizi/Film/Yayın:[/bold yellow] [dim]F12 ➔ Ağ (Network) ➔ 'm3u8' linkini yapıştırın.[/dim]")

    panel = Panel(
        grid,
        title="[bold cyan]🎬 MP4 DOWNLOADER[/bold cyan]",
        subtitle="[dim]Çıkış: 'q' • Masaüstü: 'klasor' • Temizle: 'cls' • Rehber: 'yardim'[/dim]",
        border_style="bright_blue",
        padding=(1, 2)
    )
    console.print(panel)
    console.print(f"[dim]📁 Kayıt Yeri: [bold underline cyan]{DOWNLOAD_DIR}[/bold underline cyan][/dim]\n")

def show_anime_guide():
    """Anime, dizi/film ve canlı yayınlardan kolayca video indirme rehberini gösterir."""
    guide_text = Text()
    guide_text.append("🎬 ANİME, FİLM, DİZİ & CANLI YAYIN İNDİRME REHBERİ\n\n", style="bold yellow")
    guide_text.append("1. F12 Taktigi (%100 Garanti Yöntem):\n", style="bold cyan")
    guide_text.append("   • Sitede F12 tuşuna basın ve 'Ağ' (Network) sekmesine gelin.\n", style="white")
    guide_text.append("   • Filtre kutucuğuna 'm3u8' veya 'mp4' yazın.\n", style="white")
    guide_text.append("   • Videoyu başlatın; altta beliren 'master.m3u8' linkine sağ tıklayıp kopyalayın.\n", style="white")
    guide_text.append("   • Buraya yapıştırın, otomatik olarak tek parça MP4 olarak iner!\n\n", style="green")
    guide_text.append("2. Player Kaynak Linki Yöntemi:\n", style="bold cyan")
    guide_text.append("   • Videonun altındaki 'Sibnet', 'Vidmoly', 'YourUpload' butonlarına tıklayın.\n", style="white")
    guide_text.append("   • Video penceresine sağ tıklayıp 'Video Bağlantısını Kopyala' deyin ve buraya yapıştırın.\n\n", style="white")
    guide_text.append("3. Uzun Yayın & Filmden Aralık (Kesit) İndirme:\n", style="bold cyan")
    guide_text.append("   • 4-5 saatlik yayınlarda tüm videoyu indirmek saatler sürebilir.\n", style="white")
    guide_text.append("   • Linki yapıştırdıktan sonra '01:00:00-02:00:00' veya '2-3' yazarak sadece\n", style="white")
    guide_text.append("     istediğiniz kısmı saniyeler içinde tertemiz MP4 olarak indirebilirsiniz!\n", style="green")
    guide_text.append("   • Dilerseniz doğrudan tek satırda da yapıştırabilirsiniz:\n", style="white")
    guide_text.append("     'https://site.com/yayin.m3u8 02:00:00-03:00:00'\n", style="yellow")
    
    panel = Panel(
        guide_text,
        title="[bold yellow]💡 İPUCU & REHBER[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)
    console.print("")

def build_ydl_options(url: str, progress_hook=None, ffmpeg_exe: str = None, browser_cookies: str = None, time_range: tuple = None) -> dict:
    """Tüm platformlar ve YouTube için en güncel, sağlam indirme parametrelerini üretir."""
    ffmpeg = ffmpeg_exe or get_ffmpeg_path()
    
    opts = {
        'paths': {
            'home': str(DOWNLOAD_DIR),
            'temp': str(TEMP_DIR),
        },
        # En yüksek kaliteli video ve sesi seçer (4K, 2K, 1080p60fps vb.) ve MP4 içine birleştirir
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': '%(title).120B [%(id)s].%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'retries': 10,
        'fragment_retries': 10,
        'file_access_retries': 5,
        'socket_timeout': 30,
        'windowsfilenames': True,
        'overwrites': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'ignoreerrors': False,
        # Düşük RAM'li sistemler için optimize edilmiş 64KB bellek tamponu
        'buffersize': 65536,
        # YouTube 2025/2026 n-sig & imza doğrulamasını çözmek için JS çalışma ortamları ve GitHub ejs kütüphanesi
        'remote_components': ['ejs:github'],
        'js_runtimes': {'deno': {}, 'node': {}, 'quickjs': {}},
        # Birleştirilen MP4 dosyasında sesin tüm cihazlarda çalması için AAC, video için sıfır CPU stream copy
        'postprocessor_args': {
            'Merger': ['-threads', '2', '-c:v', 'copy', '-c:a', 'aac']
        },
        # YouTube için çoklu istemci fallback zinciri
        'extractor_args': {
            'youtube': {
                'player_client': ['default', 'web', 'tv_embedded'],
            },
            'youtubetab': {
                'skip': ['authcheck'],
            }
        },
    }
    
    if time_range:
        import yt_dlp
        start_sec, end_sec = time_range
        opts['download_ranges'] = yt_dlp.utils.download_range_func([], [[start_sec, end_sec]])
        # ÖNEMLİ: force_keyframes_at_cuts = False ve -c copy ile CPU kullanımı %0 olur!
        # Video yeniden x264 ile CPU'da işlenmez; akış doğrudan kopyalanarak 50 kat hızlı iner.
        opts['force_keyframes_at_cuts'] = False
        opts['downloader_args'] = {
            'ffmpeg': ['-c', 'copy']
        }
        s_lbl = format_duration_compact(start_sec)
        e_lbl = format_duration_compact(end_sec)
        opts['outtmpl'] = f'%(title).100B [%(id)s] [{s_lbl}-{e_lbl}].%(ext)s'
        
    if progress_hook:
        opts['progress_hooks'] = [progress_hook]
        
    if ffmpeg:
        opts['ffmpeg_location'] = ffmpeg
        
    if browser_cookies:
        opts['cookiesfrombrowser'] = (browser_cookies, )
        
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        opts['impersonate'] = ImpersonateTarget.from_str('chrome')
    except Exception:
        pass
        
    url_lower = url.lower()
    if any(p in url_lower for p in ['tiktok.com', 'instagram.com', 'twitter.com', 'x.com', 'fb.watch', 'facebook.com', 'pinterest.com', 'pin.it']):
        opts['format'] = 'best[ext=mp4]/best'
        
    return opts

def download_single_video(url: str, time_range_input: str = None):
    """Tek bir video için detaylı bilgi kartı, aralık seçimi ve indirme süreci."""
    platform, color = detect_platform(url)
    ffmpeg_exe = get_ffmpeg_path()
    
    console.print(f"\n[{color}]● Platform:[/{color}] [bold {color}]{platform}[/bold {color}]")
    console.print("[dim]⏳ Video bilgileri alınıyor...[/dim]")
    
    import yt_dlp
    
    # 1. Video bilgilerini çek
    info_opts = build_ydl_options(url, ffmpeg_exe=ffmpeg_exe)
    video_info = None
    
    try:
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as de:
        err_msg = str(de)
        if any(k in err_msg.lower() for k in ["sign in", "bot", "login", "private", "age", "confirm your age"]):
            console.print("[yellow]⚠️ Giriş/Bot doğrulaması gerekti, tarayıcı oturumuyla deneniyor...[/yellow]")
            for b in ['chrome', 'edge', 'brave', 'firefox', 'opera']:
                try:
                    cookie_opts = build_ydl_options(url, ffmpeg_exe=ffmpeg_exe, browser_cookies=b)
                    with yt_dlp.YoutubeDL(cookie_opts) as ydl:
                        video_info = ydl.extract_info(url, download=False)
                    info_opts = cookie_opts
                    break
                except Exception:
                    continue
        if not video_info:
            console.print(f"[bold red]❌ Video bilgisi alınamadı:[/bold red] {err_msg}\n")
            return
    except Exception as e:
        console.print(f"[bold red]❌ Video bilgisi alınamadı:[/bold red] {e}\n")
        return

    if not video_info:
        console.print("[bold red]❌ Video bilgisi alınamadı. Link geçersiz veya video gizli olabilir.[/bold red]\n")
        return

    title = video_info.get('title', 'Bilinmeyen Video')
    uploader = video_info.get('uploader') or video_info.get('channel') or video_info.get('creator') or 'Bilinmiyor'
    total_duration = video_info.get('duration')
    duration_str = format_duration(total_duration)
    resolution = video_info.get('resolution') or f"{video_info.get('width', '?')}x{video_info.get('height', '?')}"

    # Detay kartını göster
    info_panel = Panel(
        f"[bold white]🎬 Başlık:[/bold white] [bold yellow]{title}[/bold yellow]\n"
        f"[bold white]📺 Kanal / Sahip:[/bold white] [white]{uploader}[/white]  •  "
        f"[bold white]⏱️ Toplam Süre:[/bold white] [bold cyan]{duration_str}[/bold cyan]  •  "
        f"[bold white]🎯 Kalite:[/bold white] [green]{resolution}[/green]",
        title=f"[bold {color}]● {platform} Video Detayı[/bold {color}]",
        border_style=color,
        padding=(0, 1)
    )
    console.print(info_panel)

    # 2. İndirme Tercihi & Zaman aralığı belirleme (kesit indirme)
    parsed_range = None
    if time_range_input:
        parsed_range = parse_time_range(time_range_input, total_duration)
        if not parsed_range:
            console.print(f"[bold yellow]⚠️ Belirtilen '{time_range_input}' aralığı anlaşılamadı.[/bold yellow]")

    if not parsed_range and not time_range_input:
        console.print("\n[bold cyan]✂️ İndirme Türünü Seçin:[/bold cyan]")
        console.print("  [bold yellow][1][/bold yellow] [bold white]Belirli Bir Zaman Aralığı (Kesit) İndir[/bold white] [dim](Örn: 2 ile 3 arası, 01:00:00-02:00:00)[/dim]")
        console.print(f"  [bold cyan][2][/bold cyan] [bold white]Videonun Tamamını İndir[/bold white] [dim]({duration_str})[/dim]")
        console.print("  [bold red][q][/bold red] [bold white]İptal Et / Geri Dön[/bold white]\n")

        while True:
            choice = Prompt.ask("[bold yellow]👉 Seçiminiz [1/2/q][/bold yellow] [dim](veya doğrudan aralık yazın: '2-3', '01:00:00-02:00:00')[/dim]", default="1").strip()
            
            if choice.lower() in ['q', 'iptal', 'cancel', 'vazgec', 'çıkış', 'cikis']:
                console.print("[yellow]İşlem iptal edildi.[/yellow]\n")
                return

            if choice == "2" or choice.lower() in ['tumu', 'tamami', 'full']:
                parsed_range = None
                break

            # Eğer kullanıcı doğrudan seçim kutusuna '2-3' veya '01:00:00-02:00:00' yazdıysa
            direct_range = parse_time_range(choice, total_duration)
            if direct_range:
                start_sec, end_sec = direct_range
                if total_duration and start_sec > total_duration:
                    console.print(f"[bold red]❌ Başlangıç süresi ({format_duration(start_sec)}) video süresinden ({duration_str}) büyük olamaz![/bold red]")
                    continue
                parsed_range = direct_range
                break

            if choice == "1" or not choice:
                while True:
                    user_range = Prompt.ask(
                        "\n[bold cyan]⏱️ İndirilecek aralığı yazın[/bold cyan] [dim](Örn: '01:00:00-02:00:00', '2-3', '10:00-20:00' | İptal: 'q')[/dim]"
                    ).strip()

                    if user_range.lower() in ['q', 'iptal', 'cancel']:
                        console.print("[yellow]İşlem iptal edildi.[/yellow]\n")
                        return

                    if not user_range:
                        console.print("[yellow]Aralık girmediniz. Tamamı indirilsin mi? (e/h)[/yellow]")
                        c = Prompt.ask("Tamamı indirilsin mi?", choices=["e", "h"], default="e")
                        if c == "e":
                            parsed_range = None
                            break
                        else:
                            continue

                    p_range = parse_time_range(user_range, total_duration)
                    if p_range:
                        start_sec, end_sec = p_range
                        if total_duration and start_sec > total_duration:
                            console.print(f"[bold red]❌ Başlangıç süresi ({format_duration(start_sec)}) video süresinden ({duration_str}) büyük olamaz![/bold red]")
                            continue
                        parsed_range = p_range
                        break
                    else:
                        console.print("[bold red]❌ Geçersiz aralık biçimi! Örnekler: '01:00:00-02:00:00', '2-3', '10:00-20:00'[/bold red]")
                break

    if parsed_range:
        start_sec, end_sec = parsed_range
        dur_diff = (end_sec - start_sec) if end_sec != float('inf') else "Kalan Bölüm"
        diff_str = format_duration(dur_diff) if isinstance(dur_diff, (int, float)) else dur_diff
        console.print(
            f"[bold green]✂️ İndirilecek Kesit:[/bold green] "
            f"[bold yellow]{format_duration(start_sec)}[/bold yellow] ➔ [bold yellow]{format_duration(end_sec)}[/bold yellow] "
            f"[dim](Süre: {diff_str})[/dim]\n"
        )
        console.print("[dim]⚡ [bold green]Hızlı & 0 CPU Yükü:[/bold green] Kesit re-encode edilmeden doğrudan akıştan kesilerek indiriliyor.[/dim]\n")
        if start_sec > 0:
            console.print(
                f"[dim]ℹ️ [bold yellow]Akış Notu:[/bold yellow] Kesit {format_duration(start_sec)} noktasından başladığı için, "
                f"program önce bu dakikaya kadar olan akışı hızla tarar. "
                f"O noktaya ulaşıldığında dosya doğrudan diske yazılmaya başlar.[/dim]\n"
            )
    else:
        console.print(f"[bold green]⬇ Videonun tamamı indiriliyor...[/bold green] [dim]({duration_str})[/dim]\n")

    console.print("[dim]💡 İndirmeyi iptal etmek için istediğiniz an [bold red]Ctrl+C[/bold red] tuşlayabilirsiniz.[/dim]\n")

    # 3. İlerleme ve Canlı İndirme Monitörü
    clean_title = os.path.basename(title)
    short_title = clean_title if len(clean_title) <= 25 else clean_title[:22] + "..."
    status_label = "✂️ Kesit İndiriliyor" if parsed_range else "⬇ İndiriliyor"

    # Tahmini dosya boyutu (MB) hesaplama (çubuğun dolması ve yüzde gösterilmesi için)
    est_total_mb = None
    target_duration = total_duration
    if parsed_range:
        s_s, e_s = parsed_range
        if e_s != float('inf'):
            target_duration = e_s - s_s
        elif total_duration:
            target_duration = total_duration - s_s

    tbr = video_info.get('tbr') or 0
    if not tbr and 'formats' in video_info:
        for f in video_info.get('formats', []):
            if f.get('tbr'):
                tbr = max(tbr, float(f['tbr']))
            elif (f.get('vbr') or 0) + (f.get('abr') or 0) > tbr:
                tbr = float((f.get('vbr') or 0) + (f.get('abr') or 0))

    if tbr and target_duration and target_duration > 0:
        est_total_mb = (target_duration * tbr * 1000) / (8 * 1024 * 1024)
    elif video_info.get('filesize'):
        full_mb = video_info['filesize'] / (1024 * 1024)
        if parsed_range and total_duration:
            est_total_mb = full_mb * (target_duration / total_duration)
        else:
            est_total_mb = full_mb
    elif video_info.get('filesize_approx'):
        full_mb = video_info['filesize_approx'] / (1024 * 1024)
        if parsed_range and total_duration:
            est_total_mb = full_mb * (target_duration / total_duration)
        else:
            est_total_mb = full_mb
    elif target_duration and target_duration > 0:
        h = video_info.get('height') or 1080
        default_kbps = 6500 if h >= 1080 else (3000 if h >= 720 else 1500)
        est_total_mb = (target_duration * default_kbps * 1000) / (8 * 1024 * 1024)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.fields[status]}", justify="left"),
        TextColumn("[bold blue]{task.fields[filename]}"),
        BarColumn(bar_width=18),
        TextColumn("[bold green]{task.fields[percent_str]}"),
        "•",
        TextColumn("[bold green]{task.fields[size_str]}"),
        "•",
        TextColumn("[bold yellow]{task.fields[speed_str]}"),
        console=console,
        transient=False
    )

    task_id = progress.add_task(
        "download",
        total=100.0 if est_total_mb else None,
        completed=0.0,
        status=status_label,
        filename=short_title,
        percent_str="0%" if est_total_mb else "",
        size_str="0.0 MB",
        speed_str="Bağlanıyor..."
    )

    stop_monitor = threading.Event()
    download_started_at = time.time()
    last_sz = [0.0]
    last_t = [time.time()]
    last_growth_time = [time.time()]
    last_path = [object()]
    smoothed_speed = [0.0]

    def file_monitor():
        nonlocal est_total_mb
        while not stop_monitor.is_set():
            time.sleep(0.4)
            try:
                now = time.time()
                current_path = _find_current_download_part(
                    [DOWNLOAD_DIR, TEMP_DIR], download_started_at
                )
                latest_size = current_path.stat().st_size if current_path else 0
                cur_mb = latest_size / (1024 * 1024)

                if current_path != last_path[0]:
                    last_path[0] = current_path
                    last_sz[0] = cur_mb
                    last_growth_time[0] = now
                else:
                    dt = now - last_t[0]
                    if dt > 0 and cur_mb > last_sz[0]:
                        inst_speed = (cur_mb - last_sz[0]) / dt
                        if smoothed_speed[0] <= 0:
                            smoothed_speed[0] = inst_speed
                        else:
                            smoothed_speed[0] = 0.6 * smoothed_speed[0] + 0.4 * inst_speed
                        last_growth_time[0] = now
                    last_sz[0] = cur_mb

                last_t[0] = now

                # Eğer başlangıç süresi varsa ve henüz diske veri yazılmadıysa (FFmpeg akışı ileri sarıyorsa)
                is_seeking = bool(parsed_range and parsed_range[0] > 0 and cur_mb < 0.2)
                if is_seeking:
                    start_label = format_duration(parsed_range[0])
                    elapsed = int(now - download_started_at)
                    progress.update(
                        task_id,
                        total=100.0,
                        completed=0.0,
                        percent_str="--%",
                        size_str="0.0 MB",
                        speed_str=f"Ağdan taranıyor ({elapsed} sn)",
                        status=f"[bold yellow]⏩ {start_label} Sarılıyor...[/bold yellow]"
                    )
                else:
                    if est_total_mb and cur_mb > est_total_mb:
                        est_total_mb = cur_mb * 1.05

                    if est_total_mb and est_total_mb > 0:
                        pct = min(99.0, (cur_mb / est_total_mb) * 100)
                        pct_text = f"{pct:.0f}%"
                        sz_text = f"{cur_mb:.1f} / {est_total_mb:.1f} MB"
                        comp_val = pct
                    else:
                        pct_text = ""
                        sz_text = f"{cur_mb:.1f} MB"
                        comp_val = 0.0

                    idle = now - last_growth_time[0]
                    if idle >= 4:
                        spd_text = f"Veri bekleniyor ({int(idle)} sn)"
                    elif smoothed_speed[0] > 0:
                        spd_text = f"{smoothed_speed[0]:.1f} MB/s"
                    else:
                        spd_text = "İndiriliyor..."

                    progress.update(
                        task_id,
                        total=100.0 if est_total_mb else None,
                        completed=comp_val if est_total_mb else None,
                        percent_str=pct_text,
                        size_str=sz_text,
                        speed_str=spd_text,
                        status=status_label
                    )
            except Exception:
                pass

    monitor_thread = threading.Thread(target=file_monitor, daemon=True)

    def yt_progress_hook(d):
        if d['status'] == 'downloading':
            tot = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            done = d.get('downloaded_bytes', 0)
            cur_mb = done / (1024 * 1024)
            tot_mb = tot / (1024 * 1024) if tot > 0 else 0
            spd = (d.get('speed') or 0) / (1024 * 1024)
            pct = (done / tot * 100) if tot > 0 else 0
            update = {
                'total': 100.0 if tot > 0 else None,
                'completed': pct if tot > 0 else None,
                'percent_str': f"{pct:.0f}%" if tot > 0 else "",
                'size_str': f"{cur_mb:.1f} / {tot_mb:.1f} MB" if tot > 0 else f"{cur_mb:.1f} MB",
                'status': status_label,
            }
            if spd > 0:
                update['speed_str'] = f"{spd:.1f} MB/s"
            progress.update(task_id, **update)
        elif d['status'] == 'finished':
            progress.update(task_id, percent_str="100%", status="[bold green]✓ Birleştiriliyor[/bold green]")

    download_opts = build_ydl_options(
        url,
        progress_hook=yt_progress_hook,
        ffmpeg_exe=ffmpeg_exe,
        browser_cookies=info_opts.get('cookiesfrombrowser', (None,))[0] if 'cookiesfrombrowser' in info_opts else None,
        time_range=parsed_range
    )

    saved_file_name = ""
    try:
        progress.start()
        monitor_thread.start()
        with yt_dlp.YoutubeDL(download_opts) as ydl:
            download_result = ydl.extract_info(url, download=True)
            
        stop_monitor.set()
        progress.update(task_id, status="[bold green]✓ Tamamlandı[/bold green]")
        progress.stop()

        if 'requested_downloads' in download_result and download_result['requested_downloads']:
            saved_file_name = download_result['requested_downloads'][0].get('filepath', '')
        else:
            saved_file_name = ydl.prepare_filename(download_result)
            if not saved_file_name.endswith('.mp4'):
                saved_file_name = os.path.splitext(saved_file_name)[0] + '.mp4'

        console.print("\n[bold green]════════════════════════════════════════════════════════════[/bold green]")
        console.print("[bold green]✓ TEBRİKLER! Video Başarıyla İndirildi! 🎉[/bold green]")
        console.print(f"[bold white]Başlık:[/bold white] [bold yellow]{title}[/bold yellow]")
        if parsed_range:
            console.print(f"[bold white]İndirilen Kesit:[/bold white] [bold cyan]{format_duration(parsed_range[0])} ➔ {format_duration(parsed_range[1])}[/bold cyan]")
        console.print(f"[bold white]Kanal / Sahip:[/bold white] [white]{uploader}[/white] • [bold white]Süre:[/bold white] [white]{duration_str}[/white] • [bold white]Çözünürlük:[/bold white] [cyan]{resolution}[/cyan]")
        if saved_file_name and os.path.exists(saved_file_name):
            file_size_mb = os.path.getsize(saved_file_name) / (1024 * 1024)
            console.print(f"[bold white]Dosya:[/bold white] [cyan]{os.path.basename(saved_file_name)}[/cyan] ({file_size_mb:.2f} MB)")
            console.print(f"[bold white]Konum:[/bold white] [dim]{saved_file_name}[/dim]")
        else:
            console.print(f"[bold white]Konum:[/bold white] [cyan]{DOWNLOAD_DIR}[/cyan]")
        console.print("[bold green]════════════════════════════════════════════════════════════[/bold green]\n")

    except KeyboardInterrupt:
        stop_monitor.set()
        if progress:
            try:
                progress.stop()
            except Exception:
                pass
        console.print("\n\n[bold yellow]⛔ İndirme işlemi kullanıcı tarafından iptal edildi.[/bold yellow]")
        # Geçici indirilen .part veya .ytdl dosyalarını temizle
        try:
            time.sleep(0.3)
            for d in [DOWNLOAD_DIR, TEMP_DIR]:
                for f in list(d.glob("*.part")) + list(d.glob("*.ytdl")):
                    try:
                        if f.is_file():
                            f.unlink(missing_ok=True)
                    except Exception:
                        pass
        except Exception:
            pass
        console.print("[dim]Geçici dosyalar temizlendi. Yeni indirme yapabilirsiniz.[/dim]\n")
        return
    except yt_dlp.utils.DownloadError as de:
        err_msg = str(de)
        console.print(f"\n[bold red]❌ İndirme Hatası:[/bold red] {err_msg}")
        if "Private video" in err_msg or "login" in err_msg.lower():
            console.print("[yellow]💡 İpucu: Bu video gizli veya giriş yapmayı gerektiriyor olabilir.[/yellow]\n")
        elif "Sign in" in err_msg:
            console.print("[yellow]💡 İpucu: Yaş kısıtlaması veya oturum açma gereksinimi var.[/yellow]\n")
    except Exception as e:
        console.print(f"\n[bold red]❌ Hata:[/bold red] {e}\n")

def download_multiple_videos(urls: list[str]):
    """Birden fazla video linkini eşzamanlı/paralel indirir."""
    console.print(f"\n[bold cyan]⚡ {len(urls)} adet video eşzamanlı olarak indiriliyor...[/bold cyan]\n")
    
    multi_progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.fields[status]}", justify="left"),
        TextColumn("[bold white]{task.description}"),
        BarColumn(bar_width=25),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        FileSizeColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
        transient=False
    )
    
    ffmpeg_exe = get_ffmpeg_path()
    last_update_times = {}
    
    def worker(url: str):
        platform, color = detect_platform(url)
        short_url = url if len(url) <= 30 else url[:27] + "..."
        task_id = multi_progress.add_task(
            description=f"[{color}][{platform}][/{color}] {short_url}",
            total=100,
            status="⏳ Bağlanıyor..."
        )
        
        def yt_hook(d):
            if d['status'] == 'downloading':
                tot = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                done = d.get('downloaded_bytes', 0)
                if tot > 0:
                    now = time.time()
                    # 12 FPS çoklu indirme sınırı, konsol kilitlenmesini engeller
                    if now - last_update_times.get(task_id, 0) > 0.08 or done >= tot:
                        last_update_times[task_id] = now
                        multi_progress.update(task_id, total=tot, completed=done, status="⬇ İndiriliyor")
            elif d['status'] == 'finished':
                multi_progress.update(task_id, status="🔄 İşleniyor...")
        
        opts = build_ydl_options(url, progress_hook=yt_hook, ffmpeg_exe=ffmpeg_exe)
        try:
            import yt_dlp
            with yt_dlp.YoutubeDL(opts) as ydl:
                download_result = ydl.extract_info(url, download=True)
                title = download_result.get('title', 'Video') if download_result else 'Video'
                short_title = title if len(title) <= 25 else title[:22] + "..."
                multi_progress.update(
                    task_id,
                    description=f"[{color}][{platform}][/{color}] {short_title}",
                    status="[bold green]✓ Tamamlandı[/bold green]",
                    completed=multi_progress.tasks[task_id].total or 100
                )
        except Exception:
            # Oturum gerektiren videolar için tarayıcı çerezi ile kurtarma
            try:
                opts_cookie = build_ydl_options(url, progress_hook=yt_hook, ffmpeg_exe=ffmpeg_exe, browser_cookies='chrome')
                with yt_dlp.YoutubeDL(opts_cookie) as ydl:
                    download_result = ydl.extract_info(url, download=True)
                    title = download_result.get('title', 'Video') if download_result else 'Video'
                    short_title = title if len(title) <= 25 else title[:22] + "..."
                    multi_progress.update(
                        task_id,
                        description=f"[{color}][{platform}][/{color}] {short_title}",
                        status="[bold green]✓ Tamamlandı[/bold green]",
                        completed=multi_progress.tasks[task_id].total or 100
                    )
            except Exception:
                multi_progress.update(task_id, status="[bold red]❌ Hata[/bold red]", completed=100)
    
    try:
        with multi_progress:
            with ThreadPoolExecutor(max_workers=5) as executor:
                list(executor.map(worker, urls))
                
        console.print("\n[bold green]✓ Tüm videolar başarıyla indirildi ve Masaüstüne kaydedildi.[/bold green]\n")
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]⛔ Çoklu indirme işlemi iptal edildi.[/bold yellow]\n")
        return

def process_input(user_input: str):
    """Kullanıcının girdiği komut, link veya zaman aralığını işler."""
    tokens = [u.strip() for u in user_input.split() if u.strip()]
    valid_urls = [u for u in tokens if u.startswith("http://") or u.startswith("https://") or "www." in u]
    
    if not valid_urls:
        console.print("[bold red]❌ Geçerli bir video linki bulunamadı! Lütfen http:// veya https:// ile başlayan bir link yapıştırın.[/bold red]\n")
        return
    
    if len(valid_urls) == 1:
        url = valid_urls[0]
        other_tokens = [t for t in tokens if t != url]
        time_range_str = " ".join(other_tokens).strip() if other_tokens else None
        download_single_video(url, time_range_input=time_range_str)
    else:
        download_multiple_videos(valid_urls)

def main():
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        if args[0].lower() in ['klasor', 'klasör', 'open', 'masaustu']:
            open_download_folder()
            return
        valid_urls = [u for u in args if u.startswith("http://") or u.startswith("https://") or "www." in u]
        if valid_urls:
            if len(valid_urls) == 1:
                url = valid_urls[0]
                other_args = [a for a in args if a != url]
                time_range_str = " ".join(other_args).strip() if other_args else None
                download_single_video(url, time_range_input=time_range_str)
            else:
                download_multiple_videos(valid_urls)
            return

    start_background_ffmpeg_check()
    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()

    while True:
        try:
            user_input = Prompt.ask("\n[bold yellow]📥 Video linki yapıştırın[/bold yellow]").strip()
            
            if not user_input:
                continue
                
            cmd = user_input.lower()
            if cmd in ['q', 'exit', 'quit', 'cikis', 'çıkış']:
                console.print("\n[bold cyan]Güle güle! Görüşmek üzere 👋[/bold cyan]\n")
                break
            elif cmd in ['klasor', 'klasör', 'open', 'desktop', 'masaustu', 'masaüstü']:
                open_download_folder()
                continue
            elif cmd in ['yardim', 'help', 'rehber', 'info', 'bilgi']:
                show_anime_guide()
                continue
            elif cmd in ['cls', 'clear', 'temizle']:
                os.system('cls' if os.name == 'nt' else 'clear')
                display_banner()
                continue
            
            process_input(user_input)
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[bold cyan]İşlem durduruldu. Görüşmek üzere 👋[/bold cyan]\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Hata: {e}[/bold red]\n")

if __name__ == "__main__":
    main()
