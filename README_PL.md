# Fuelio dla Home Assistant

Niestandardowa integracja odczytująca eksport CSV aplikacji Fuelio. Obsługuje dwa warianty źródła:
- **Lokalny plik CSV** — np. w katalogu `/config/fuelio/`.
- **Google Drive** — przez zewnętrzną synchronizację pliku do Home Assistant, np. rclone na osobnym LXC i udział SMB. Integracja nie łączy się bezpośrednio z Google Drive ani nie przechowuje tokenów Google.

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

Nie wpisuj danych OAuth Google do konfiguracji integracji.

## Encje

Integracja tworzy sensory dotyczące:
- przebiegu i ostatniego tankowania,
- ceny paliwa i ostatniego obliczonego spalania,
- średniego spalania z zapisanych wartości Fuelio,
- kosztu i ilości paliwa w bieżącym miesiącu oraz roku,
- łącznych kosztów eksploatacyjnych,
- najbliższego przypomnienia według przebiegu,
- liczby wpisów tankowań i kosztów.

Identyfikatory encji mogą zostać zmienione przez Home Assistant, jeśli istnieją już encje o podobnych nazwach.

## Aktualizacja

Integracja ponownie odczytuje CSV w zadanym interwale. Po zastąpieniu pliku nowym eksportem dane zostaną odczytane przy kolejnym odświeżeniu. Nie jest wymagany restart HA.

## Obliczenia i ograniczenia

- Średnie spalanie to średnia arytmetyczna dodatnich wartości z kolumny `l/100km (optional)`.
- Wartość 0.0 w polu spalania jest traktowana jako brak wyliczenia.
- Koszty paliwa są sumowane z kolumny `Price (optional)`.
- Najbliższe przypomnienie jest wybierane na podstawie `RemindOdo`, jeśli jest większe od aktualnego przebiegu.
- Przypomnienia kalendarzowe z `RemindDate` nie są obecnie obsługiwane.

## Prywatność

Eksport Fuelio może zawierać VIN, numer rejestracyjny, współrzędne GPS i notatki. Integracja nie publikuje tych pól jako sensorów i nie przesyła pliku poza Home Assistant. Nie commituj prywatnego eksportu CSV do repozytorium.
