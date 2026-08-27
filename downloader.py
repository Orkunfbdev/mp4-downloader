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
    import yt_dlp
except ImportError:
    print("\n[!] Gerekli kütüphaneler eksik. Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.\n")
    sys.exit(1)

# Pillow kontrolü
try:
    from PIL import Image, ImageEnhance, ImageFilter
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# FFmpeg yolunu belirle
def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(ffmpeg_exe):
            return ffmpeg_exe
    except Exception:
        pass
    return None

console = Console(force_terminal=True, legacy_windows=False)

# Dizinler
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = Path.home() / "Desktop"
if not DOWNLOAD_DIR.exists():
    DOWNLOAD_DIR = Path.home() / "Masaüstü"
DOWNLOAD_DIR.mkdir(exist_ok=True)

TEMP_DIR = Path(os.environ.get('TEMP', str(DOWNLOAD_DIR))) / "mp4_downloader_temp"
TEMP_DIR.mkdir(exist_ok=True)

ASSETS_DIR = BASE_DIR / "assets"
OBITO_IMG_PATH = ASSETS_DIR / "obito.jpg"

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

def get_obito_ansi_image(width=44, height=24):
    """Obito resmini yüksek çözünürlük ve gerçek RGB renklerle ANSI metnine dönüştürür."""
    if not HAS_PIL or not OBITO_IMG_PATH.exists():
        return None
    try:
        img = Image.open(OBITO_IMG_PATH).convert('RGB')
        img = ImageEnhance.Contrast(img).enhance(1.4)
        img = ImageEnhance.Sharpness(img).enhance(2.2)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        
        lines = []
        for y in range(0, height, 2):
            line = ""
            for x in range(width):
                r1, g1, b1 = img.getpixel((x, y))
                r2, g2, b2 = img.getpixel((x, y+1)) if y+1 < height else (0, 0, 0)
                line += f"\x1b[38;2;{r1};{g1};{b1}m\x1b[48;2;{r2};{g2};{b2}m▀\x1b[0m"
            lines.append(line)
        return Text.from_ansi("\n".join(lines))
    except Exception:
        return None

def display_banner():
    obito_img_text = get_obito_ansi_image(width=44, height=24)
    
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
    
    def yt_progress_hook(d):
        nonlocal task_id
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            filename = os.path.basename(d.get('filename', 'Video'))
            if len(filename) > 30:
                filename = filename[:27] + "..."
            
            if task_id is None:
                task_id = progress.add_task("download", total=total_bytes, filename=filename)
                progress.start()
            
            if total_bytes > 0:
                progress.update(task_id, total=total_bytes, completed=downloaded, filename=filename)
        elif d['status'] == 'finished':
            if task_id is not None:
                progress.update(task_id, completed=progress.tasks[task_id].total)
                progress.stop()
    
    ydl_opts = {
        'paths': {
            'home': str(DOWNLOAD_DIR),
            'temp': str(TEMP_DIR),
        },
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
        'outtmpl': '%(title).120B [%(id)s].%(ext)s',
        'merge_output_format': 'mp4',
        'progress_hooks': [yt_progress_hook],
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'ignoreerrors': False,
        'windowsfilenames': True,
        'overwrites': True,
        'nocheckcertificate': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['tr', 'tr-.*', 'tur', 'Turkish', 'en', 'all'],
        'postprocessors': [
            {'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': False},
        ],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
        },
    }
    
    try:
        from yt_dlp.networking.impersonate import ImpersonateTarget
        ydl_opts['impersonate'] = ImpersonateTarget.from_str('chrome')
    except Exception:
        pass
    
    if ffmpeg_exe:
        ydl_opts['ffmpeg_location'] = ffmpeg_exe

    if "tiktok.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif "instagram.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif "twitter.com" in url.lower() or "x.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'

    saved_file_name = ""
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                console.print("[bold red]❌ Video bilgisi alınamadı. Link geçersiz veya video gizli olabilir.[/bold red]\n")
                return
            
            title = info.get('title', 'Bilinmeyen Video')
            uploader = info.get('uploader') or info.get('channel') or info.get('creator') or 'Bilinmiyor'
            duration = format_duration(info.get('duration'))
            resolution = info.get('resolution') or f"{info.get('width', '?')}x{info.get('height', '?')}"
            
            # Bilgi Kartı
            table = Table(title="📹 Video Detayları", show_header=False, border_style="blue", padding=(0, 1))
            table.add_column("Özellik", style="bold yellow", width=14)
            table.add_column("Değer", style="white")
            
            table.add_row("Başlık", str(title))
            table.add_row("Kanal / Sahip", str(uploader))
            table.add_row("Süre", str(duration))
            table.add_row("Çözünürlük", str(resolution))
            
            console.print(table)
            console.print("[bold green]⬇ İndirme işlemi başlatılıyor...[/bold green]\n")
            
            download_result = ydl.extract_info(url, download=True)
            
            if 'requested_downloads' in download_result and download_result['requested_downloads']:
                saved_file_name = download_result['requested_downloads'][0].get('filepath', '')
            else:
                saved_file_name = ydl.prepare_filename(download_result)
                if not saved_file_name.endswith('.mp4'):
                    saved_file_name = os.path.splitext(saved_file_name)[0] + '.mp4'

        console.print("\n[bold green]════════════════════════════════════════════════════════════[/bold green]")
        console.print("[bold green]✓ TEBRİKLER! Video Başarıyla İndirildi! 🎉[/bold green]")
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
                    multi_progress.update(task_id, total=tot, completed=done, status="⬇ İndiriliyor")
            elif d['status'] == 'finished':
                multi_progress.update(task_id, status="🔄 İşleniyor...")
        
        opts = {
            'paths': {'home': str(DOWNLOAD_DIR), 'temp': str(TEMP_DIR)},
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
            'outtmpl': '%(title).120B [%(id)s].%(ext)s',
            'merge_output_format': 'mp4',
            'progress_hooks': [yt_hook],
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'ignoreerrors': False,
            'windowsfilenames': True,
            'overwrites': True,
            'nocheckcertificate': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['tr', 'tr-.*', 'tur', 'Turkish', 'en', 'all'],
            'postprocessors': [
                {'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': False},
            ],
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
            },
        }
        try:
            from yt_dlp.networking.impersonate import ImpersonateTarget
            opts['impersonate'] = ImpersonateTarget.from_str('chrome')
        except Exception:
            pass
        if ffmpeg_exe:
            opts['ffmpeg_location'] = ffmpeg_exe
        if "tiktok.com" in url.lower() or "instagram.com" in url.lower() or "twitter.com" in url.lower() or "x.com" in url.lower():
            opts['format'] = 'best[ext=mp4]/best'
            
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video') if info else 'Video'
                short_title = title if len(title) <= 25 else title[:22] + "..."
                multi_progress.update(
                    task_id,
                    description=f"[{color}][{platform}][/{color}] {short_title}",
                    status="⬇ İndiriliyor..."
                )
                ydl.extract_info(url, download=True)
                multi_progress.update(task_id, status="[bold green]✓ Tamamlandı[/bold green]", completed=multi_progress.tasks[task_id].total or 100)
        except Exception as e:
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

    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()
    
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        console.print("[yellow]⚠️ Uyarı: FFmpeg motoru bulunamadı. Bazı 1080p/4K videolarda ses birleştirme sınırlı olabilir.[/yellow]\n")
    else:
        console.print("[green]✓ FFmpeg video motoru aktif.[/green]\n")

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
