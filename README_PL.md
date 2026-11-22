# Fuelio dla Home Assistant

Custom integration odczytująca eksport CSV aplikacji Fuelio. Obsługuje dwa warianty źródła:
- **Lokalny plik CSV** — np. w katalogu `/config/fuelio/`.
- **Google Drive** — przez zewnętrzną synchronizację pliku do Home Assistant, np. rclone i SMB. Integracja nie łączy się bezpośrednio z Google Drive ani nie przechowuje tokenów Google.

## Instalacja ręczna

1. Utwórz katalog `/config/custom_components/fuelio/`.
2. Skopiuj do niego zawartość katalogu `custom_components/fuelio` z repozytorium.
3. Zrestartuj Home Assistant.
4. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wyszukaj **Fuelio**.
5. Wybierz źródło danych:
   - **Lokalny plik CSV** — domyślna ścieżka `/config/fuelio/vehicle-1-sync.csv`.
   - **Google Drive (zsynchronizowany plik / SMB)** — domyślna ścieżka `/share/Fuelio/vehicle-1-sync.csv`.
6. Wskaż ścieżkę i interwał odświeżania (domyślnie 5 minut).

### Google Drive przez rclone i SMB

Integracja czyta wyłącznie rozpakowany plik CSV widoczny w systemie plików Home Assistant. Synchronizację ZIP z Google Drive, rozpakowanie i udostępnienie pliku przez SMB należy skonfigurować niezależnie. Przykładowy przepływ:

`Google Drive → rclone → rozpakowanie CSV → udział SMB → /share/Fuelio/vehicle-1-sync.csv → Fuelio`

Szczegółowa instrukcja konfiguracji kontenera LXC, Google OAuth, rclone, skryptu synchronizacji, timera systemd, Samby i montowania udziału w Home Assistant znajduje się w pliku [docs/GOOGLE_DRIVE_RCLONE_PL.md](docs/GOOGLE_DRIVE_RCLONE_PL.md).

Nie wpisuj danych OAuth Google do konfiguracji integracji.

## Encje

Integracja tworzy sensory dotyczące:
- przebiegu i ostatniego tankowania,
- ceny paliwa i ostatniego obliczonego spalania,
- średniego spalania z zapisanych wartości Fuelio,
- kosztu i ilości paliwa w bieżącym miesiącu oraz roku,
- łącznych kosztów eksploatacyjnych,
- najbliższego przypomnienia według przebiegu,
- najbliższego przypomnienia kalendarzowego (data i nazwa),
- ostatniego wpisu kosztowego: nazwa, kwota, data i kategoria,
- liczby tankowań i wpisów kosztowych.

Sensor **Liczba wpisów kosztowych** udostępnia pełną historię wpisów w atrybucie `cost_history`. Każdy wpis zawiera nazwę, datę, kategorię, koszt, przebieg oraz ustawione przypomnienia.

## Przypomnienia i koszty

- Przypomnienia przebiegowe są wybierane na podstawie `RemindOdo`, jeśli wartość jest większa od aktualnego przebiegu.
- Przypomnienia kalendarzowe są wybierane na podstawie przyszłej daty `RemindDate`, niezależnie od `RemindOdo`. Wpis z `RemindOdo=0` nadal może więc wywołać przypomnienie kalendarzowe.
- Ostatni wpis kosztowy jest wybierany według daty wpisu w sekcji `## Costs`.
- Wpisy z kosztem 0 pozostają widoczne w historii i mogą być przypomnieniami, ale nie zwiększają sum kosztów eksploatacyjnych.

Identyfikatory encji mogą zostać zmienione przez Home Assistant, jeśli istnieją już encje o podobnych nazwach.

## Aktualizacja

Integracja ponownie odczytuje CSV w zadanym interwale. Po zastąpieniu pliku nowym eksportem dane zostaną odczytane przy kolejnym odświeżeniu. Nie jest wymagany restart HA po podmianie samego pliku. Po aktualizacji kodu integracji należy zrestartować Home Assistant.

## Obliczenia i ograniczenia

- Średnie spalanie to średnia arytmetyczna dodatnich wartości z kolumny `l/100km (optional)`.
- Wartość 0.0 w polu spalania jest traktowana jako brak wyliczenia.
- Koszty paliwa są sumowane z kolumny `Price (optional)`.
- Koszty eksploatacyjne sumują wyłącznie dodatnie wartości z kolumny `Cost`; wpisy zerowe są zachowane w historii.
- Przypomnienia kalendarzowe i przebiegowe są prezentowane oddzielnie.

## Prywatność

Eksport Fuelio może zawierać VIN, numer rejestracyjny, współrzędne GPS i notatki. Integracja nie publikuje tych pól jako sensorów i nie przesyła pliku poza Home Assistant. Nie commituj prywatnego eksportu CSV do repozytorium.
