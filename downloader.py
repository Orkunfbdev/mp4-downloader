import os
import sys
import time
import threading
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
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, FileSizeColumn, SpinnerColumn
    from rich.text import Text
    from rich.align import Align
    from rich.live import Live
    from rich.layout import Layout
    import yt_dlp
except ImportError:
    print("\n[!] Gerekli kütüphaneler eksik. Lütfen 'pip install -r requirements.txt' komutunu çalıştırın.\n")
    sys.exit(1)

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

# İndirme klasörü (Masaüstü / Desktop)
def get_desktop_dir():
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        return desktop
    desktop_tr = Path.home() / "Masaüstü"
    if desktop_tr.exists():
        return desktop_tr
    return Path.home() / "Desktop"

DOWNLOAD_DIR = get_desktop_dir()
DOWNLOAD_DIR.mkdir(exist_ok=True)

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
    """İndirilenler (Masaüstü) klasörünü Windows Gezgini'nde açar."""
    try:
        os.startfile(str(DOWNLOAD_DIR))
        console.print(f"[bold green]✓ Masaüstü açıldı:[/bold green] [cyan]{DOWNLOAD_DIR}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Klasör açılamadı: {e}[/red]\n")

def display_banner():
    banner_text = Text()
    banner_text.append("═══════════════════════════════════════════════════════════════\n", style="bold cyan")
    banner_text.append("             🎬 TÜM PLATFORMLAR MP4 İNDİRİCİ 🎬                \n", style="bold yellow")
    banner_text.append("     YouTube • TikTok • Twitter (X) • Instagram • 1000+ Site   \n", style="bold white")
    banner_text.append("     ⚡ Eşzamanlı Çoklu İndirme Desteği Aktif                  \n", style="bold green")
    banner_text.append("═══════════════════════════════════════════════════════════════", style="bold cyan")
    
    panel = Panel(
        Align.center(banner_text),
        subtitle="[dim]Çıkış: 'q' • Masaüstünü Aç: 'klasor' • Ekranı Temizle: 'cls'[/dim]",
        border_style="bright_blue",
        padding=(0, 1)
    )
    console.print(panel)
    console.print(f"[dim]📁 Kayıt Yeri: [bold underline]{DOWNLOAD_DIR}[/bold underline][/dim]\n")

# Global çoklu indirme ilerleme çubuğu yöneticisi
shared_progress = Progress(
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
    transient=False,
    refresh_per_second=10
)

# Eşzamanlı indirmeler için thread havuzu
executor = ThreadPoolExecutor(max_workers=6)
active_downloads_count = 0
downloads_lock = threading.Lock()

TEMP_DIR = Path(os.environ.get('TEMP', str(DOWNLOAD_DIR))) / "mp4_downloader_temp"
TEMP_DIR.mkdir(exist_ok=True)

def download_task_worker(url: str):
    global active_downloads_count
    with downloads_lock:
        active_downloads_count += 1
    
    platform, color = detect_platform(url)
    ffmpeg_exe = get_ffmpeg_path()
    
    # Progress task ekle
    short_url = url if len(url) <= 35 else url[:32] + "..."
    task_id = shared_progress.add_task(
        description=f"[{color}][{platform}][/{color}] {short_url}",
        total=100,
        status="⏳ Bağlanıyor..."
    )
    
    def yt_progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                shared_progress.update(
                    task_id,
                    total=total_bytes,
                    completed=downloaded,
                    status="⬇ İndiriliyor"
                )
        elif d['status'] == 'finished':
            shared_progress.update(
                task_id,
                status="🔄 İşleniyor/MP4..."
            )
    
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
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
        },
    }
    
    if ffmpeg_exe:
        ydl_opts['ffmpeg_location'] = ffmpeg_exe

    if "tiktok.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif "instagram.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'
    elif "twitter.com" in url.lower() or "x.com" in url.lower():
        ydl_opts['format'] = 'best[ext=mp4]/best'

    saved_file_name = ""
    title = ""
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            shared_progress.update(task_id, status="🔍 Bilgi alınıyor...")
            info = ydl.extract_info(url, download=False)
            if not info:
                shared_progress.update(task_id, status="❌ [bold red]Hata (Link geçersiz)[/bold red]", completed=100)
                return
            
            title = info.get('title', 'Video')
            short_title = title if len(title) <= 30 else title[:27] + "..."
            shared_progress.update(
                task_id,
                description=f"[{color}][{platform}][/{color}] {short_title}",
                status="⬇ İndiriliyor..."
            )
            
            download_result = ydl.extract_info(url, download=True)
            
            if 'requested_downloads' in download_result and download_result['requested_downloads']:
                saved_file_name = download_result['requested_downloads'][0].get('filepath', '')
            else:
                saved_file_name = ydl.prepare_filename(download_result)
                if not saved_file_name.endswith('.mp4'):
                    saved_file_name = os.path.splitext(saved_file_name)[0] + '.mp4'

        shared_progress.update(
            task_id,
            completed=shared_progress.tasks[task_id].total or 100,
            status="[bold green]✓ Tamamlandı[/bold green]"
        )
        
        file_size_str = ""
        if saved_file_name and os.path.exists(saved_file_name):
            file_size_mb = os.path.getsize(saved_file_name) / (1024 * 1024)
            file_size_str = f" ({file_size_mb:.1f} MB)"
            
        console.print(f"\n[bold green]✓ [Masaüstü][/bold green] [white]{title}[/white][green]{file_size_str}[/green] başarıyla kaydedildi!")
        
    except Exception as e:
        err_str = str(e)
        if len(err_str) > 60:
            err_str = err_str[:57] + "..."
        shared_progress.update(task_id, status=f"[bold red]❌ {err_str}[/bold red]", completed=100)
        console.print(f"\n[bold red]❌ İndirme Başarısız:[/bold red] {url} -> [dim]{e}[/dim]")
    finally:
        with downloads_lock:
            active_downloads_count -= 1

def queue_download(url: str):
    """İndirme işlemini arkaplan iş parçacığına gönderir."""
    executor.submit(download_task_worker, url)

def interactive_loop():
    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()
    
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        console.print("[yellow]⚠️ Uyarı: FFmpeg motoru bulunamadı. Bazı 1080p/4K videolarda ses birleştirme sınırlı olabilir.[/yellow]\n")
    else:
        console.print("[green]✓ FFmpeg video işleme motoru aktif.[/green]\n")

    # Shared progress'i başlat
    shared_progress.start()

    try:
        while True:
            try:
                console.print("[bold yellow]📥 Video linki yapıştırın[/bold yellow] [dim](Birden fazla link atabilir, inerken yenisini ekleyebilirsiniz)[/dim]:", end=" ")
                user_input = sys.stdin.readline()
                if not user_input:
                    break
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                    
                cmd = user_input.lower()
                if cmd in ['q', 'exit', 'quit', 'cikis', 'çıkış']:
                    if active_downloads_count > 0:
                        console.print(f"\n[yellow]⏳ Arkaplanda devam eden {active_downloads_count} indirme var. Tamamlanmaları bekleniyor...[/yellow]")
                        executor.shutdown(wait=True)
                    console.print("\n[bold cyan]Güle güle! Görüşmek üzere 👋[/bold cyan]\n")
                    break
                elif cmd in ['klasor', 'klasör', 'open', 'desktop', 'masaustu', 'masaüstü']:
                    open_download_folder()
                    continue
                elif cmd in ['cls', 'clear', 'temizle']:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    display_banner()
                    continue
                
                # Boşlukla ayrılmış birden fazla link girildiyse hepsini kuyruğa al
                urls = [u.strip() for u in user_input.split() if u.strip()]
                for u in urls:
                    if u.startswith("http://") or u.startswith("https://") or "www." in u:
                        queue_download(u)
                    else:
                        console.print(f"[bold red]❌ Geçersiz link formatı:[/bold red] {u}")
                
                time.sleep(0.3)
                
            except (KeyboardInterrupt, EOFError):
                if active_downloads_count > 0:
                    console.print(f"\n[yellow]⏳ Devam eden {active_downloads_count} indirme tamamlanıyor...[/yellow]")
                    executor.shutdown(wait=True)
                console.print("\n[bold cyan]Çıkış yapıldı. 👋[/bold cyan]\n")
                break
            except Exception as e:
                console.print(f"\n[bold red]Hata: {e}[/bold red]\n")
    finally:
        shared_progress.stop()

def main():
    # Komut satırı argümanı kontrolü (Örn: indir https://... https://...)
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        # Özel komutlar kontrolü
        if args[0].lower() in ['klasor', 'klasör', 'open', 'masaustu']:
            open_download_folder()
            return
        
        shared_progress.start()
        try:
            for url in args:
                if url.startswith("http://") or url.startswith("https://") or "www." in url:
                    queue_download(url)
                else:
                    console.print(f"[bold red]❌ Geçersiz link:[/bold red] {url}")
            
            # Tüm indirmeler bitene kadar bekle
            executor.shutdown(wait=True)
        finally:
            shared_progress.stop()
    else:
        interactive_loop()

if __name__ == "__main__":
    main()
