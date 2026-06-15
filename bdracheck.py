import os
import json
from typing import Any, Dict
import click

# Scaffolding configuration blueprints
DEFAULT_CONFIG: Dict[str, Any] = {
    "architecture_spec": "BDRA-Lite-v1",
    "strict_mode": True,
    "enforce_mypy": True,
    "monitored_rings": ["ring0", "ring1", "ring2"]
}

@click.group()
def cli() -> None:
    """BDRA-Lite Architecture Compliance & Developer Experience Toolkit."""
    pass


@cli.command()
@click.option("--force", is_flag=True, help="Overwrite existing bdracheck.json configuration.")
def init(force: bool) -> None:
    """Initializes the project workspace with compliance metadata configuration."""
    config_path = "bdracheck.json"
    
    if os.path.exists(config_path) and not force:
        click.secho("⚠️  bdracheck.json already exists in this workspace! Use --force to overwrite.", fg="yellow")
        return
        
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
        
    click.secho("✅ Initialized BDRA-Lite architecture workspace configuration config (bdracheck.json).", fg="green", bold=True)


@cli.command(name="new-ring")
@click.argument("domain_name")
@click.option("--ring", default="1", type=click.Choice(["0", "1", "2"]), help="Target architecture ring isolation level.")
def new_ring(domain_name: str, ring: str) -> None:  # 👈 Changed type hint from int to str
    """Scaffolds a compliant multi-tier sub-domain workspace structure."""
    # Clean and normalize domain name inputs
    clean_domain = domain_name.lower().strip().replace("-", "_")
    base_dir = f"app/internal/ring{ring}/{clean_domain}"
    
    # Enforce strict architecture directory patterns
    sub_layers = ["pure", "protected", "public"]
    
    click.echo(f"🏗️  Scaffolding architecture structure for domain '{clean_domain}' in Ring {ring}...")
    
    for layer in sub_layers:
        target_path = os.path.join(base_dir, layer)
        os.makedirs(target_path, exist_ok=True)
        
        # Inject package initialization hooks to satisfy Mypy and Python imports
        init_file = os.path.join(target_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write(f'# BDRA-Lite Generated Scaffolding: Ring {ring} -> {clean_domain} -> {layer}\n')
                
        click.echo(f"   └── Created: {target_path}")

    # Inject package boundary marker at the domain root level
    root_init = os.path.join(base_dir, "__init__.py")
    if not os.path.exists(root_init):
        with open(root_init, "w", encoding="utf-8") as f:
            f.write("# Sub-domain package boundary layer\n")

    click.secho(f"\n🚀 Success! Domain '{clean_domain}' structural interfaces ready for engineering implementation.", fg="green", bold=True)


if __name__ == "__main__":
    cli()