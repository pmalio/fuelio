# Synchronizacja Fuelio z Google Drive przez rclone i SMB

Ten poradnik opisuje wariant, w którym aplikacja Fuelio automatycznie wysyła archiwum ZIP do Google Drive, a osobny kontener LXC pobiera je przez `rclone`, rozpakowuje CSV i udostępnia plik Home Assistant przez SMB.

Integracja Fuelio **nie łączy się bezpośrednio z Google Drive**. Odczytuje gotowy plik CSV z lokalnego udziału sieciowego.

## Schemat działania

```text
Fuelio na Androidzie
       |
       | automatyczna synchronizacja ZIP
       v
Google Drive: Android/Fuelio/sync/vehicle-1-sync.csv.zip
       |
       | rclone (co 15 minut)
       v
Kontener LXC Debian: /srv/fuelio/vehicle-1-sync.csv
       |
       | Samba / SMB
       v
Home Assistant: /share/Fuelio/vehicle-1-sync.csv
       |
       v
Integracja Fuelio
```

Przykładowa konfiguracja z tego poradnika:
- Proxmox VE z kontenerem LXC Debian 12.
- Adres kontenera synchronizującego: `192.168.8.3` (u Ciebie może być inny).
- Zdalny katalog Google Drive: `Android/Fuelio/sync`.
- Nazwa archiwum: `vehicle-1-sync.csv.zip`.
- Katalog lokalny na LXC: `/srv/fuelio`.
- Nazwa udziału SMB: `fuelio`.
- Częstotliwość synchronizacji: co 15 minut.

Dostosuj adres IP, nazwy i ścieżki do własnej sieci oraz eksportu Fuelio.

---

## 1. Przygotuj kontener LXC w Proxmox

Utwórz kontener Debian 12 (amd64). Przykładowe zasoby wystarczające dla samej synchronizacji:
- 1 rdzeń CPU,
- 512 MB RAM,
- 4 GB dysku,
- interfejs sieciowy podłączony do mostu LAN,
- stały adres IP lub rezerwacja DHCP.

W dalszych poleceniach zakładamy, że kontener ma adres `192.168.8.3`. Zaloguj się do kontenera jako `root`.

Zaktualizuj system i zainstaluj potrzebne narzędzia:

```bash
apt update
apt upgrade -y
apt install -y curl unzip samba
```

Utwórz katalogi:

```bash
mkdir -p /opt/fuelio-sync /srv/fuelio
```

## 2. Skonfiguruj dostęp rclone do Google Drive

### 2.1. Utwórz projekt OAuth Google

W przeglądarce otwórz [Google Cloud Console](https://console.cloud.google.com/).

1. Utwórz projekt, np. `Fuelio Sync`.
2. Wybierz ten projekt.
3. W sekcji **APIs & Services → Library** znajdź i włącz **Google Drive API**.
4. Przejdź do **Google Auth Platform** (lub ekranu konfiguracji OAuth).
5. Skonfiguruj ekran zgody OAuth. Dla prywatnego konta wybierz typ użytkowników **External**, jeśli jest wymagany.
6. Podaj nazwę aplikacji i adres e-mail kontaktowy.
7. Jeżeli aplikacja pozostaje w trybie testowym, dodaj własne konto Google jako użytkownika testowego.

### 2.2. Utwórz klienta OAuth

1. W sekcji **Clients** utwórz klienta OAuth typu **Desktop app**.
2. Zapisz Client ID i Client Secret. Nie publikuj ich i nie wklejaj do repozytorium.
3. Jeśli aplikacja jest pozostawiona w trybie **Testing**, odświeżające tokeny dla zewnętrznych aplikacji testowych mogą wygasać po 7 dniach. Do stałej pracy skonfiguruj odpowiedni status publikacji aplikacji zgodnie z zasadami Google. Przy aplikacji niezweryfikowanej Google może pokazywać ostrzeżenie podczas autoryzacji; nie omijaj ostrzeżeń, jeśli nie masz pewności, komu udzielasz dostępu.

> Google okresowo zmienia nazwy i układ ekranów OAuth. Kieruj się aktualnym interfejsem Google Cloud Console. Nigdy nie udostępniaj Client Secret ani pliku tokena.

### 2.3. Zainstaluj rclone

Zainstaluj aktualne wydanie rclone zgodnie z instrukcją na [rclone.org/install](https://rclone.org/install/). Dla Debiana można użyć oficjalnego instalatora:

```bash
curl https://rclone.org/install.sh | bash
rclone version
```

### 2.4. Utwórz zdalne połączenie `fuelio`

Uruchom kreator:

```bash
rclone config
```

W kreatorze:
1. Wybierz `n` — nowe połączenie.
2. Nazwij je `fuelio`.
3. Jako typ magazynu wybierz **Google Drive**.
4. Wprowadź własny Client ID i Client Secret utworzone w Google Cloud.
5. Wybierz zakres tylko do odczytu, jeśli dostępny jest wybór zakresu (w aktualnym kreatorze rclone jest to opcja `2`, zwykle opisana jako read-only).
6. Pozostałe ustawienia pozostaw domyślne, o ile nie masz szczególnego powodu, by je zmieniać.
7. Jeśli kreator zapyta o automatyczną konfigurację w przeglądarce, na maszynie bez GUI wybierz konfigurację zdalną / ręczną zgodnie z komunikatem rclone.
8. Na komputerze z przeglądarką uruchom wskazane przez rclone polecenie autoryzacyjne, zaloguj się do właściwego konta Google i zaakceptuj dostęp.
9. Przenieś wynik autoryzacji/token do kreatora rclone w kontenerze, jeśli kreator tego wymaga, i zapisz konfigurację.

Nie wklejaj tokena do dokumentacji, repozytorium ani publicznego zgłoszenia.

Sprawdź, czy połączenie działa:

```bash
rclone lsd fuelio:
rclone lsjson fuelio:Android/Fuelio/sync --max-depth 2
```

W katalogu powinno być widoczne archiwum `vehicle-1-sync.csv.zip`. Jeśli Fuelio zapisuje eksport w innym folderze lub pod inną nazwą, popraw ścieżkę w skrypcie z następnego kroku.

## 3. Przygotuj skrypt pobierający i rozpakowujący CSV

Utwórz plik:

```bash
nano /usr/local/bin/fuelio-sync.sh
```

Wklej:

```bash
#!/usr/bin/env bash
set -euo pipefail

REMOTE="fuelio:Android/Fuelio/sync/vehicle-1-sync.csv.zip"
DIR="/srv/fuelio"
TMPZIP="$DIR/vehicle-1-sync.csv.zip.tmp"
TMPCSV="$DIR/vehicle-1-sync.csv.tmp"

mkdir -p "$DIR"

# Pobierz archiwum do pliku tymczasowego.
rclone copyto "$REMOTE" "$TMPZIP"

# Sprawdź archiwum i wyodrębnij CSV do pliku tymczasowego.
unzip -tq "$TMPZIP"
unzip -p "$TMPZIP" vehicle-1-sync.csv > "$TMPCSV"
test -s "$TMPCSV"

# Podmień pliki dopiero po poprawnym pobraniu i rozpakowaniu.
mv "$TMPZIP" "$DIR/vehicle-1-sync.csv.zip"
mv "$TMPCSV" "$DIR/vehicle-1-sync.csv"

echo "Fuelio CSV updated successfully."
```

Zapisz plik i nadaj mu prawo wykonywania:

```bash
chmod 750 /usr/local/bin/fuelio-sync.sh
```

Uruchom test ręczny:

```bash
/usr/local/bin/fuelio-sync.sh
ls -lh /srv/fuelio/
```

Powinny pojawić się:
- `vehicle-1-sync.csv`,
- `vehicle-1-sync.csv.zip`.

Jeśli archiwum zawiera CSV w podkatalogu, a nie w katalogu głównym ZIP, popraw nazwę ścieżki w poleceniu `unzip -p`.

Skrypt najpierw pobiera i sprawdza plik tymczasowy. Dotychczasowy CSV jest podmieniany dopiero po udanym pobraniu i rozpakowaniu, dzięki czemu błąd synchronizacji nie powinien nadpisać działającego pliku pustym lub niekompletnym eksportem.

## 4. Ustaw automatyczne uruchamianie co 15 minut

Utwórz usługę systemd:

```bash
nano /etc/systemd/system/fuelio-sync.service
```

Treść:

```ini
[Unit]
Description=Synchronize Fuelio CSV from Google Drive
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fuelio-sync.sh
```

Utwórz timer:

```bash
nano /etc/systemd/system/fuelio-sync.timer
```

Treść:

```ini
[Unit]
Description=Run Fuelio synchronization every 15 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
```

Wczytaj konfigurację i włącz timer:

```bash
systemctl daemon-reload
systemctl enable --now fuelio-sync.timer
```

Sprawdź status:

```bash
systemctl status fuelio-sync.timer
systemctl list-timers fuelio-sync.timer
```

Ręczne uruchomienie usługi:

```bash
systemctl start fuelio-sync.service
```

Logi ostatniego uruchomienia:

```bash
journalctl -u fuelio-sync.service -n 50 --no-pager
```

## 5. Udostępnij katalog przez SMB (Samba)

Utwórz użytkownika systemowego i konto Samby:

```bash
useradd -M -s /usr/sbin/nologin fuelio
smbpasswd -a fuelio
```

Podczas `smbpasswd` ustaw hasło. Będzie potrzebne przy dodawaniu zasobu w Home Assistant.

Otwórz konfigurację:

```bash
nano /etc/samba/smb.conf
```

Na końcu pliku dodaj:

```ini
[fuelio]
   path = /srv/fuelio
   browseable = yes
   read only = yes
   guest ok = no
   valid users = fuelio
   hosts allow = 192.168.8.0/24
```

Dostosuj podsieć w `hosts allow` do własnej sieci LAN. Ograniczenie dostępu do sieci lokalnej jest zalecane.

Sprawdź konfigurację i uruchom Sambę:

```bash
testparm
systemctl enable --now smbd
systemctl restart smbd
systemctl status smbd
```

Konto udziału ma dostęp tylko do odczytu. Nie udostępniaj Samby bezpośrednio do Internetu.

## 6. Dodaj udział sieciowy w Home Assistant

W interfejsie Home Assistant:

1. Otwórz **Ustawienia → System → Pamięć / Storage**.
2. Wybierz **Dodaj pamięć sieciową / Add network storage**.
3. Wprowadź:
   - **Nazwa:** `Fuelio`
   - **Typ:** Samba / Windows (CIFS)
   - **Serwer:** adres IP kontenera LXC, np. `192.168.8.3`
   - **Udział:** `fuelio`
   - **Użytkownik:** `fuelio`
   - **Hasło:** hasło ustawione przez `smbpasswd`
   - **Zastosowanie / Usage:** Share
4. Zapisz konfigurację.

Po zamontowaniu Home Assistant powinien udostępnić katalog jako:

```text
/share/Fuelio/
```

Sprawdź w dodatku Terminal & SSH:

```bash
ls -lah /share/Fuelio/
```

Oczekiwane pliki:

```text
vehicle-1-sync.csv
vehicle-1-sync.csv.zip
```

Sprawdź, czy CSV nie jest pusty:

```bash
test -s /share/Fuelio/vehicle-1-sync.csv && echo "CSV jest dostępny"
```

Jeżeli katalog nie istnieje lub jest pusty, sprawdź konfigurację udziału sieciowego w Home Assistant, adres IP, nazwę udziału, dane logowania oraz logi `smbd` w kontenerze LXC.

## 7. Skonfiguruj integrację Fuelio

Podczas dodawania integracji wybierz źródło:

**Google Drive (zsynchronizowany plik / SMB)**

Domyślna ścieżka:

```text
/share/Fuelio/vehicle-1-sync.csv
```

Ustaw interwał odświeżania integracji, np. 5 minut. Synchronizacja rclone działa niezależnie co 15 minut, więc integracja odczyta nowy plik przy kolejnym swoim odświeżeniu.

## 8. Diagnostyka

### Czy rclone widzi plik w Google Drive?

```bash
rclone lsjson fuelio:Android/Fuelio/sync --max-depth 2
```

### Czy synchronizacja działa ręcznie?

```bash
systemctl start fuelio-sync.service
journalctl -u fuelio-sync.service -n 50 --no-pager
ls -lh /srv/fuelio/
```

### Czy timer jest aktywny?

```bash
systemctl status fuelio-sync.timer
systemctl list-timers fuelio-sync.timer
```

### Czy Samba działa?

```bash
testparm
systemctl status smbd
journalctl -u smbd -n 50 --no-pager
```

### Czy Home Assistant widzi plik?

W Terminal & SSH:

```bash
ls -lh /share/Fuelio/
```

### Typowe przyczyny problemów

- **rclone zwraca błąd autoryzacji:** ponownie sprawdź konfigurację remote `fuelio` i autoryzację OAuth.
- **Nie znaleziono pliku:** sprawdź nazwę archiwum i ścieżkę folderu na Google Drive.
- **Błąd rozpakowywania:** sprawdź, czy archiwum ZIP zawiera plik `vehicle-1-sync.csv` pod oczekiwaną nazwą.
- **Brak katalogu w HA:** sprawdź montowanie SMB w ustawieniach pamięci sieciowej HA.
- **Dane nie odświeżają się od razu:** uwzględnij osobne interwały timera rclone (15 min) i integracji (np. 5 min).

## 9. Bezpieczeństwo i kopie zapasowe

- Nie umieszczaj Client Secret, tokenów OAuth, haseł Samby ani pliku `rclone.conf` w repozytorium.
- Ogranicz dostęp do kontenera LXC i jego plików konfiguracyjnych. Plik rclone zawiera dane umożliwiające dostęp do Google Drive.
- Używaj zakresu Google Drive tylko do odczytu.
- Nie wystawiaj portów SMB (TCP 445/139) do Internetu.
- Eksport Fuelio może zawierać dane osobowe i lokalizacyjne (np. VIN, numer rejestracyjny, współrzędne GPS). Traktuj CSV i ZIP jako dane prywatne.
- Uwzględnij katalog `/etc/rclone` lub lokalizację wskazaną przez `rclone config file` w planie kopii zapasowej kontenera. Zabezpiecz kopię, ponieważ zawiera token.
- Nie commituj prawdziwych eksportów Fuelio do repozytorium Git.
