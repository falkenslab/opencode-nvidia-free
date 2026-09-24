# CLAUDE.md

Este repositorio es un **experimento** del [Cuaderno del Dr. Falken](https://github.com/falkenslab/falkens-notebook). Su objetivo es demostrar o refutar una idea con código ejecutable y resultados reales. El cuaderno recoge después los resultados con `/harvest`, así que la estructura es un contrato: respétala.

## Estructura

- `README.md` — secciones fijas: **Idea, Hipótesis, Requisitos, Cómo ejecutar, Resultados, Conclusiones**. No las renombres ni las quites; `/harvest` las lee por nombre.
- `ENV.md` — entorno exacto de cada ejecución (SO, hardware, versiones, modelos).
- `results/` — salida real y sin editar, con fecha en el nombre del fichero.
- `src/` — el código del experimento.

## Reglas

- **Nunca inventes resultados.** Si algo no se puede ejecutar en esta máquina, dilo y pide que lo ejecute una persona. Un resultado inventado invalida el experimento.
- Cada ejecución deja su salida en `results/` y su entorno en `ENV.md`, con la misma fecha.
- Los fallos también son resultados: guarda el log y explícalo en Conclusiones.
- Secretos y claves en `.env`, nunca en el repo.
- Idioma: español.
- Cuando el experimento esté terminado, crea un tag (`v1`) para que el cuaderno cite un commit fijo.
