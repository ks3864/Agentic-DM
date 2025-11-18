## Installation

Ensure you have Python >=3.10 <3.14 and `uv` installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling.

Add API key(s) in the `.env` file.

```

## Running

Run from the root folder of the project:

```bash
$ crewai run
```

### TODO
- Modify `src/agenticdm/config/agents.yaml` to define your agents
- Modify `src/agenticdm/config/tasks.yaml` to define your tasks
- Modify `src/agenticdm/crew.py` to add your own logic, tools and specific args
- Modify `src/agenticdm/main.py` to add custom inputs for your agents and tasks