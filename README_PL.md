# Fuelio dla Home Assistant

Niestandardowa integracja odczytująca lokalny eksport CSV aplikacji Fuelio. Integracja nie łączy się bezpośrednio z Google Drive, nie modyfikuje pliku źródłowego i nie wysyła danych poza Home Assistant.

## Instalacja ręczna

1. Utwórz katalog `/config/custom_components/fuelio/`.
2. Skopiuj do niego zawartość katalogu `custom_components/fuelio` z repozytorium.
3. Utwórz katalog `/config/fuelio/`.
4. Rozpakuj archiwum eksportu Fuelio i umieść plik CSV w `/config/fuelio/vehicle-1-sync.csv`.
5. Zrestartuj Home Assistant.
6. Otwórz **Ustawienia → Urządzenia i usługi → Dodaj integrację** i wyszukaj **Fuelio**.
7. Wskaż ścieżkę `/config/fuelio/vehicle-1-sync.csv` i interwał odświeżania (domyślnie 5 minut).

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

Integracja ponownie odczytuje CSV w zadanym interwale. Aby wczytać nowe tankowanie, zastąp plik nowym eksportem Fuelio. Nie jest wymagany restart HA.

## Obliczenia i ograniczenia

- Średnie spalanie to średnia arytmetyczna dodatnich wartości z kolumny `l/100km (optional)`.
- Wartość 0.0 w polu spalania jest traktowana jako brak wyliczenia.
- Koszty paliwa są sumowane z kolumny `Price (optional)`.
- Najbliższe przypomnienie jest wybierane na podstawie `RemindOdo`, jeśli jest większe od aktualnego przebiegu.
- Przypomnienia kalendarzowe z `RemindDate` nie są obecnie obsługiwane.
- Automatyczna synchronizacja z Google Drive/Android nie jest częścią tej wersji.

## Prywatność

Eksport Fuelio może zawierać VIN, numer rejestracyjny, współrzędne GPS i notatki. Integracja nie publikuje tych pól jako sensorów i nie przesyła pliku poza Home Assistant. Nie commituj prywatnego eksportu CSV do repozytorium.
