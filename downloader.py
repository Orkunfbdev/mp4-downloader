import os
import sys
import time
import subprocess
from pathlib import Path

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
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn, FileSizeColumn
    from rich.text import Text
    from rich.align import Align
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
    """Linkten platformu ve uygun emoji/renk bilgisini döner."""
    url_lower = url.lower()
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "YouTube", "red"
    elif "tiktok.com" in url_lower:
        return "TikTok", "magenta"
    elif "instagram.com" in url_lower:
        return "Instagram", "bright_magenta"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "Twitter / X", "cyan"
    elif "facebook.com" in url_lower or "fb.watch" in url_lower:
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
    """İndirilenler klasörünü Windows Gezgini'nde açar."""
    try:
        os.startfile(str(DOWNLOAD_DIR))
        console.print(f"[bold green]✓ İndirilenler klasörü açıldı:[/bold green] [cyan]{DOWNLOAD_DIR}[/cyan]\n")
    except Exception as e:
        console.print(f"[red]Klasör açılamadı: {e}[/red]\n")

def display_banner():
    banner_text = Text()
    banner_text.append("══════════════════════════════════════════════════════════\n", style="bold cyan")
    banner_text.append("           🎬 TÜM PLATFORMLAR MP4 İNDİRİCİ 🎬             \n", style="bold yellow")
    banner_text.append("      YouTube • TikTok • Twitter (X) • Instagram • Web    \n", style="bold white")
    banner_text.append("══════════════════════════════════════════════════════════", style="bold cyan")
    
    panel = Panel(
        Align.center(banner_text),
        subtitle="[dim]Hazır • Çıkış: 'q' • Klasörü Aç: 'klasor' • Ekranı Temizle: 'cls'[/dim]",
        border_style="bright_blue",
        padding=(0, 1)
    )
    console.print(panel)
    console.print(f"[dim]📁 Kayıt Yeri: [bold underline]{DOWNLOAD_DIR}[/bold underline][/dim]\n")

def download_video(url: str):
    platform, color = detect_platform(url)
    ffmpeg_exe = get_ffmpeg_path()
    
    console.print(f"\n[{color}]● Algılanan Platform:[/{color}] [bold {color}]{platform}[/bold {color}]")
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
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best',
        'outtmpl': str(DOWNLOAD_DIR / '%(title).120B [%(id)s].%(ext)s'),
        'merge_output_format': 'mp4',
        'progress_hooks': [yt_progress_hook],
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'ignoreerrors': False,
        'windowsfilenames': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,tr;q=0.8',
        },
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    if ffmpeg_exe:
        ydl_opts['ffmpeg_location'] = ffmpeg_exe

    # Özel platform format ayarları
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
            
            # Bilgi Kartı Tablosu
            table = Table(title="📹 Video Detayları", show_header=False, border_style="blue", padding=(0, 1))
            table.add_column("Özellik", style="bold yellow", width=14)
            table.add_column("Değer", style="white")
            
            table.add_row("Başlık", str(title))
            table.add_row("Kanal / Sahip", str(uploader))
            table.add_row("Süre", str(duration))
            table.add_row("Çözünürlük", str(resolution))
            
            console.print(table)
            console.print("[bold green]⬇ İndirme işlemi başlatılıyor...[/bold green]\n")
            
            # Gerçek indirmeyi yap
            download_result = ydl.extract_info(url, download=True)
            
            # İndirilen dosya adı
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
            console.print("[yellow]💡 İpucu: Bu video gizli veya giriş yapmayı gerektiriyor olabilir.[/yellow]")
        elif "Sign in" in err_msg:
            console.print("[yellow]💡 İpucu: Yaş kısıtlaması veya oturum açma gereksinimi var.[/yellow]")
        console.print("")
    except Exception as e:
        console.print(f"\n[bold red]❌ Beklenmeyen bir hata oluştu:[/bold red] {e}\n")

def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    display_banner()
    
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        console.print("[yellow]⚠️ Uyarı: FFmpeg motoru bulunamadı. Bazı 1080p/4K YouTube videolarında ses birleştirme sınırlı olabilir.[/yellow]\n")
    else:
        console.print("[green]✓ FFmpeg video işleme motoru aktif.[/green]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold yellow]📥 Video linkini yapıştırın[/bold yellow] [dim]('q'=çıkış, 'klasor'=klasörü aç)[/dim]").strip()
            
            if not user_input:
                continue
                
            cmd = user_input.lower()
            if cmd in ['q', 'exit', 'quit', 'cikis', 'çıkış']:
                console.print("\n[bold cyan]Güle güle! Görüşmek üzere 👋[/bold cyan]\n")
                break
            elif cmd in ['klasor', 'klasör', 'open', 'downloads', 'folder']:
                open_download_folder()
                continue
            elif cmd in ['cls', 'clear', 'temizle']:
                os.system('cls' if os.name == 'nt' else 'clear')
                display_banner()
                continue
            
            # URL kontrolü
            if not (user_input.startswith("http://") or user_input.startswith("https://") or "www." in user_input):
                console.print("[bold red]❌ Geçerli bir web linki girmediniz! Lütfen http:// veya https:// ile başlayan bir link yapıştırın.[/bold red]\n")
                continue
            
            download_video(user_input)
            
        except (KeyboardInterrupt, EOFError):
            console.print("\n\n[bold cyan]İşlem kullanıcı tarafından durduruldu. Görüşmek üzere 👋[/bold cyan]\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Hata: {e}[/bold red]\n")

if __name__ == "__main__":
    main()
