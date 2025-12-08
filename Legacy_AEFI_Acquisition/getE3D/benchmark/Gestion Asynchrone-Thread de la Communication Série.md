MOC : [[MOC ACQUISITION]] [[MOC INSTRUMENTATION]]
Source : 
Projets : [[PROJET ASSOCE]] [[PROJET Banc de Test Python]]
Tags : #Readme 
Date : 2025-06-10
Liens : - [[Caractérisation des Performances de Communication Série pour le Banc d'Acquisition DDS-ADC ADS131 GREYC]]
***
## 1. Introduction et Intérêt de l'Asynchronisme

Dans les systèmes d'acquisition rapide, la communication série synchrone (mode bloquant) atteint rapidement ses limites : la latence cumulée, le risque de blocage du programme principal et la difficulté à garantir un flux continu de données peuvent dégrader les performances globales. L'utilisation d'une gestion asynchrone (ou multi-threadée) permet de découpler l'envoi/réception des commandes du reste du traitement logiciel, offrant ainsi :

- Une meilleure réactivité de l'interface utilisateur
- Une réduction du risque de perte de données (overflow)
- Une meilleure stabilité temporelle (jitter réduit)
- La possibilité de traiter les données en parallèle de leur acquisition

## 2. Principes de la Communication Asynchrone

- **Thread dédié** : Un thread séparé gère la lecture/écriture sur le port série, pendant que le thread principal s'occupe de la logique métier ou de l'interface graphique.
- **Queues (files d'attente)** : Les commandes à envoyer et les réponses reçues sont stockées dans des files thread-safe (par exemple `queue.Queue` en Python).
- **Non-blocage** : Le thread principal n'attend jamais la fin d'une opération série ; il dépose une commande dans la queue et continue son exécution.
- **Gestion des erreurs** : Les erreurs de communication sont remontées via une queue dédiée ou des callbacks.

## 3. Stratégie de Mise en Place dans le Code

### 3.1 Architecture proposée

- **Trois queues** :
  - `cmd_queue` : commandes à envoyer
  - `response_queue` : réponses reçues
  - `error_queue` : erreurs détectées
- **Un thread de communication** qui :
  - Récupère les commandes dans `cmd_queue`
  - Les envoie sur le port série
  - Lit les réponses et les place dans `response_queue`
  - Capture les erreurs et les place dans `error_queue`
- **Le thread principal** :
  - Dépose les commandes à envoyer dans `cmd_queue`
  - Récupère les réponses dans `response_queue` quand il en a besoin
  - Peut surveiller `error_queue` pour la robustesse

### 3.2 Exemple de Structure en Python

```python
from threading import Thread, Lock
from queue import Queue, Empty
import serial
import time

class SerialAsyncManager:
    def __init__(self, port, baudrate):
        self.ser = serial.Serial(port, baudrate, timeout=2)
        self.cmd_queue = Queue()
        self.response_queue = Queue()
        self.error_queue = Queue()
        self.running = False
        self.thread = None
        self.lock = Lock()

    def start(self):
        self.running = True
        self.thread = Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.ser.close()

    def _worker(self):
        while self.running:
            try:
                if not self.cmd_queue.empty():
                    with self.lock:
                        cmd = self.cmd_queue.get(block=False)
                        if not cmd.endswith('*'):
                            cmd += '*'
                        self.ser.write(cmd.encode())
                        response = self.ser.readline().decode().strip()
                        self.response_queue.put((cmd, response))
                time.sleep(0.01)
            except Exception as e:
                self.error_queue.put(str(e))

    def send_command(self, command):
        self.cmd_queue.put(command)

    def get_response(self, block=False, timeout=None):
        try:
            return self.response_queue.get(block=block, timeout=timeout)
        except Empty:
            return None

    def get_error(self, block=False, timeout=None):
        try:
            return self.error_queue.get(block=block, timeout=timeout)
        except Empty:
            return None
```

### 3.3 Points d'attention
- Toujours protéger l'accès au port série par un verrou (`Lock`) si plusieurs threads peuvent y accéder.
- Adapter la gestion des timeouts et la taille des queues selon le débit attendu.
- Prévoir un mécanisme de flush/vidage des queues pour éviter l'accumulation en cas de surcharge.
- Surveiller la consommation mémoire si le flux de données est très important.

## 4. Conclusion

La gestion asynchrone de la communication série est une étape clé pour fiabiliser et optimiser les performances d'un banc d'acquisition rapide. Sa mise en œuvre, bien que nécessitant une architecture logicielle plus élaborée, permet de garantir la robustesse et la scalabilité du système, en particulier lors de sweeps ou d'acquisitions longues et intensives. 