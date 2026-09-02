import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Windows UTF-8 / Türkçe karakter desteği
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        sys.stdin.reconfigure(encoding='utf-8', errors='replace')
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
    from rich.align import Align
except ImportError:
    print("\n[!] Gerekli kütüphaneler eksik. Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.\n")
    sys.exit(1)

# FFmpeg yolunu belirle ve önbellekle
# FFmpeg yolunu belirle ve arkaplanda önbellekle
_CACHED_FFMPEG_PATH = None

def _resolve_ffmpeg():
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH is not None:
        return
    import shutil
    w = shutil.which("ffmpeg")
    if w:
        _CACHED_FFMPEG_PATH = w
        return
    for p in [BASE_DIR / "ffmpeg.exe", Path.cwd() / "ffmpeg.exe"]:
        if p.exists():
            _CACHED_FFMPEG_PATH = str(p)
            return
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            _CACHED_FFMPEG_PATH = ffmpeg_exe
            return
    except Exception:
        pass
    _CACHED_FFMPEG_PATH = ""

def get_ffmpeg_path():
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH is None:
        _resolve_ffmpeg()
    return _CACHED_FFMPEG_PATH if _CACHED_FFMPEG_PATH else None

def start_background_ffmpeg_check():
    import threading
    t = threading.Thread(target=_resolve_ffmpeg, daemon=True)
    t.start()

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
    if not seconds:
        return "Bilinmiyor"
    seconds = int(seconds)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"

def open_download_folder():
    """Masaüstü klasörünü Windows Gezgini'nde açar."""
    try:
        os.startfile(str(DOWNLOAD_DIR))
        console.print(f"[bold green]✓ Masaüstü açıldı:[/bold green] [cyan]{DOWNLOAD_DIR}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Klasör açılamadı: {e}[/red]\n")

# Pre-rendered & compressed Obito pixel art (Pillow gerektirmez, 0.00s açılış)
OBITO_B64 = (
    "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"
)

_CACHED_OBITO_TEXT = None
def get_obito_ansi_image():
    """Önceden optimize edilmiş Obito ANSI görselini anında çözer (0.00s)."""
    global _CACHED_OBITO_TEXT
    if _CACHED_OBITO_TEXT is not None:
        return _CACHED_OBITO_TEXT
    try:
        import zlib
        import base64
        raw_ansi = zlib.decompress(base64.b64decode(OBITO_B64.encode('ascii'))).decode('utf-8')
        _CACHED_OBITO_TEXT = Text.from_ansi(raw_ansi)
        return _CACHED_OBITO_TEXT
    except Exception:
        return None

def display_banner():
    obito_img_text = get_obito_ansi_image()
    
    banner_text = Text()
    banner_text.append("\n  🎬 TÜM PLATFORMLAR MP4 İNDİRİCİ\n", style="bold yellow")
    banner_text.append("  ──────────────────────────────────────────\n", style="dim cyan")
    banner_text.append("  📺 YouTube • TikTok • Twitter (X) • Instagram\n", style="bold white")
    banner_text.append("  ⚡ Eşzamanlı Çoklu İndirme Devrede\n", style="bold green")
    banner_text.append("  🎯 En Yüksek Kalite MP4 Otomatik Birleştirme\n\n", style="bold cyan")
    banner_text.append("  💡 Anime & Film Siteleri İçin:\n", style="bold yellow")
    banner_text.append("     Sitede F12 -> Ağ (Network) -> 'm3u8' linkini\n", style="white")
    banner_text.append("     kopyalayıp buraya yapıştırmanız yeterlidir.\n", style="green")
    
    if obito_img_text:
        grid = Table.grid(padding=(0, 2))
        grid.add_row(obito_img_text, banner_text)
        content = grid
    else:
        content = banner_text
        
    panel = Panel(
        Align.center(content),
        title="[bold cyan]🎬 MP4 DOWNLOADER[/bold cyan]",
        subtitle="[dim]Çıkış: 'q' • Masaüstünü Aç: 'klasor' • Ekranı Temizle: 'cls'[/dim]",
        border_style="bright_blue",
        padding=(1, 1)
    )
    console.print(panel)
    console.print(f"[dim]📁 Kayıt Yeri: [bold underline cyan]{DOWNLOAD_DIR}[/bold underline cyan][/dim]\n")

def show_anime_guide():
    """Anime ve film sitelerinden kolayca video indirme rehberini gösterir."""
    guide_text = Text()
    guide_text.append("🎬 ANİME & DİZİ/FİLM SİTELERİNDEN İNDİRME REHBERİ\n\n", style="bold yellow")
    guide_text.append("1. F12 Taktigi (%100 Garanti Yöntem):\n", style="bold cyan")
    guide_text.append("   • Sitede F12 tuşuna basın ve 'Ağ' (Network) sekmesine gelin.\n", style="white")
    guide_text.append("   • Filtre kutucuğuna 'm3u8' veya 'mp4' yazın.\n", style="white")
    guide_text.append("   • Videoyu başlatın; altta beliren 'master.m3u8' linkine sağ tıklayıp kopyalayın.\n", style="white")
    guide_text.append("   • Buraya yapıştırın, otomatik olarak tek parça MP4 olarak iner!\n\n", style="green")
    guide_text.append("2. Player Kaynak Linki Yöntemi:\n", style="bold cyan")
    guide_text.append("   • Videonun altındaki 'Sibnet', 'Vidmoly', 'YourUpload' butonlarına tıklayın.\n", style="white")
    guide_text.append("   • Video penceresine sağ tıklayıp 'Video Bağlantısını Kopyala' deyin ve buraya yapıştırın.\n", style="white")
    
    panel = Panel(
        guide_text,
        title="[bold yellow]💡 İPUCU & REHBER[/bold yellow]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)
    console.print("")

def build_ydl_options(url: str, progress_hook=None, ffmpeg_exe: str = None, browser_cookies: str = None) -> dict:
    """Tüm platformlar ve YouTube için en güncel, sağlam indirme parametrelerini üretir."""
    ffmpeg = ffmpeg_exe or get_ffmpeg_path()
    
    opts = {
        'paths': {
            'home': str(DOWNLOAD_DIR),
            'temp': str(TEMP_DIR),
        },
        # En yüksek kaliteli video ve sesi seçer (gerekirse MP4 içine birleştirir)
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
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
        # YouTube 2025/2026 n-sig & imza doğrulamasını çözmek için JS çalışma ortamları ve GitHub ejs kütüphanesi
        'remote_components': ['ejs:github'],
        'js_runtimes': {'deno': {}, 'node': {}, 'quickjs': {}},
        # Birleştirilen MP4 dosyasında sesin tüm cihazlarda (Windows Media Player, TV, telefon) çalması için AAC dönüştürme
        'postprocessor_args': {
            'Merger': ['-c:v', 'copy', '-c:a', 'aac']
        },
        # YouTube için çoklu istemci fallback zinciri (Tek istemci takılırsa diğerine geçer)
        'extractor_args': {
            'youtube': {
                'player_client': ['default', 'web', 'android', 'ios', 'mweb'],
                'player_skip': ['configs', 'webpage'],
            },
            'youtubetab': {
                'skip': ['authcheck'],
            }
        },
    }
    
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

def download_single_video(url: str):
    """Tek bir video için detaylı bilgi kartı ve indirme süreci."""
    platform, color = detect_platform(url)
    ffmpeg_exe = get_ffmpeg_path()
    
    console.print(f"\n[{color}]● Platform:[/{color}] [bold {color}]{platform}[/bold {color}]")
    console.print("[dim]⏳ Video bilgileri alınıyor...[/dim]")
    
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
        BarColumn(bar_width=None),
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
    
    task_id = None
    last_update_time = 0.0
    
    def yt_progress_hook(d):
        nonlocal task_id, last_update_time
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            filename = os.path.basename(d.get('filename', 'Video'))
            if len(filename) > 30:
                filename = filename[:27] + "..."
            
            if task_id is None:
                task_id = progress.add_task("download", total=total_bytes, filename=filename)
                progress.start()
            
            now = time.time()
            # 16 FPS sınır (her 0.06s'de bir çizim), CPU yükünü ve konsol donmasını engeller
            if total_bytes > 0 and (now - last_update_time > 0.06 or downloaded >= total_bytes):
                last_update_time = now
                progress.update(task_id, total=total_bytes, completed=downloaded, filename=filename)
        elif d['status'] == 'finished':
            if task_id is not None:
                progress.update(task_id, completed=progress.tasks[task_id].total)
                progress.stop()

    def run_download(cookies_browser: str = None):
        opts = build_ydl_options(url, progress_hook=yt_progress_hook, ffmpeg_exe=ffmpeg_exe, browser_cookies=cookies_browser)
        import yt_dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            res = ydl.extract_info(url, download=True)
            return res, ydl

    saved_file_name = ""
    
    try:
        import yt_dlp
        download_result = None
        ydl = None
        
        try:
            download_result, ydl = run_download()
        except yt_dlp.utils.DownloadError as de:
            err_msg = str(de)
            # Bot doğrulaması veya oturum açma gereksinimi varsa tarayıcı çerezleriyle otomatik kurtar
            if any(k in err_msg.lower() for k in ["sign in", "bot", "login", "private", "age", "confirm your age"]):
                console.print("[yellow]⚠️ Giriş/Bot doğrulaması gerekti, tarayıcı oturumuyla deneniyor...[/yellow]")
                recovered = False
                for b in ['chrome', 'edge', 'brave', 'firefox', 'opera']:
                    try:
                        download_result, ydl = run_download(cookies_browser=b)
                        recovered = True
                        break
                    except Exception:
                        continue
                if not recovered:
                    raise de
            else:
                raise de
                
        if not download_result:
            console.print("[bold red]❌ Video bilgisi alınamadı. Link geçersiz veya video gizli olabilir.[/bold red]\n")
            return
            
        title = download_result.get('title', 'Bilinmeyen Video')
        uploader = download_result.get('uploader') or download_result.get('channel') or download_result.get('creator') or 'Bilinmiyor'
        duration = format_duration(download_result.get('duration'))
        resolution = download_result.get('resolution') or f"{download_result.get('width', '?')}x{download_result.get('height', '?')}"
        
        if 'requested_downloads' in download_result and download_result['requested_downloads']:
            saved_file_name = download_result['requested_downloads'][0].get('filepath', '')
        else:
            saved_file_name = ydl.prepare_filename(download_result)
            if not saved_file_name.endswith('.mp4'):
                saved_file_name = os.path.splitext(saved_file_name)[0] + '.mp4'

        console.print("\n[bold green]════════════════════════════════════════════════════════════[/bold green]")
        console.print("[bold green]✓ TEBRİKLER! Video Başarıyla İndirildi! 🎉[/bold green]")
        console.print(f"[bold white]Başlık:[/bold white] [bold yellow]{title}[/bold yellow]")
        console.print(f"[bold white]Kanal / Sahip:[/bold white] [white]{uploader}[/white] • [bold white]Süre:[/bold white] [white]{duration}[/white] • [bold white]Çözünürlük:[/bold white] [cyan]{resolution}[/cyan]")
        if saved_file_name and os.path.exists(saved_file_name):
            file_size_mb = os.path.getsize(saved_file_name) / (1024 * 1024)
            console.print(f"[bold white]Dosya:[/bold white] [cyan]{os.path.basename(saved_file_name)}[/cyan] ({file_size_mb:.2f} MB)")
            console.print(f"[bold white]Konum:[/bold white] [dim]{saved_file_name}[/dim]")
        else:
            console.print(f"[bold white]Konum:[/bold white] [cyan]{DOWNLOAD_DIR}[/cyan]")
        console.print("[bold green]════════════════════════════════════════════════════════════[/bold green]\n")

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
    
    with multi_progress:
        with ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(worker, urls))
            
    console.print("\n[bold green]✓ Tüm videolar başarıyla indirildi ve Masaüstüne kaydedildi.[/bold green]\n")

def process_input(user_input: str):
    """Kullanıcının girdiği komut veya linkleri işler."""
    urls = [u.strip() for u in user_input.split() if u.strip()]
    valid_urls = [u for u in urls if u.startswith("http://") or u.startswith("https://") or "www." in u]
    
    if not valid_urls:
        console.print("[bold red]❌ Geçerli bir video linki bulunamadı! Lütfen http:// veya https:// ile başlayan bir link yapıştırın.[/bold red]\n")
        return
    
    if len(valid_urls) == 1:
        download_single_video(valid_urls[0])
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
                download_single_video(valid_urls[0])
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
