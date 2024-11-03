import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable

# 1. Simulando os dados
np.random.seed(123)
n = 50  # Número de corretores
vendedores = pd.DataFrame({
    'id': range(1, n + 1),
    'vendas': np.random.normal(100, 30, n),  # Gerando vendas médias
    'lat': np.random.uniform(-23.7, -23.4, n),  # Coordenadas de latitude (exemplo de São Paulo)
    'long': np.random.uniform(-46.7, -46.4, n)  # Coordenadas de longitude
})

# Convertendo para GeoDataFrame com o CRS geográfico
vendedores_gdf = gpd.GeoDataFrame(vendedores, geometry=gpd.points_from_xy(vendedores['long'], vendedores['lat']), crs="EPSG:4326")

# Reprojetando para um CRS projetado adequado (exemplo: UTM para São Paulo)
vendedores_gdf = vendedores_gdf.to_crs(epsg=32723)  # UTM zona 23S, CRS para área de São Paulo

# 2. Filtrando os top vendedores com base nas vendas
top_vendedores = vendedores_gdf[vendedores_gdf['vendas'] > vendedores_gdf['vendas'].quantile(0.75)]

# 3. Visualização da Animação
fig, ax = plt.subplots(figsize=(10, 8))

# Mapeamento de cores
norm = Normalize(vmin=top_vendedores['vendas'].min(), vmax=top_vendedores['vendas'].max())
cmap = plt.get_cmap('plasma')  # Paleta de cores plasma
sm = ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])

# Cria a barra de cores e a legenda fora da função de atualização
cbar = fig.colorbar(sm, ax=ax, orientation='vertical')
cbar.set_label('Volume de Vendas', fontsize=12)
ax.legend(['Corretores', 'Área de Influência'], loc='upper left', fontsize=12)

def update(frame):
    ax.clear()
    ax.set_title(f'Região dos Top Vendedores - Reamostragem Bootstrap: {frame + 1}', fontsize=14)

    # Amostra com reposição dos top vendedores
    sample_indices = np.random.choice(top_vendedores.index, size=len(top_vendedores), replace=True)
    sample = top_vendedores.loc[sample_indices].copy()

    # Criando o buffer com raio proporcional ao volume de vendas
    sample['geometry'] = sample.geometry.buffer(sample['vendas'] * 10 * (frame + 1) / 10)  # Ajuste do tamanho do buffer

    # Reprojetando de volta para o CRS geográfico para plotagem
    sample = sample.to_crs("EPSG:4326")
    vendedores_gdf_geo = vendedores_gdf.to_crs("EPSG:4326")

    # Plota os corretores originais
    vendedores_gdf_geo.plot(ax=ax, color='darkred', markersize=10, zorder=3)

    # Plota os buffers da amostra atual
    for _, row in sample.iterrows():
        buffer = row['geometry']
        vendas = row['vendas']
        color = cmap(norm(vendas))  # Mapeia a cor com base nas vendas
        gpd.GeoSeries(buffer).plot(ax=ax, color=color, alpha=0.5, edgecolor='black', linewidth=1.5, zorder=2)

    # Ajuste o eixo para focar na área dos pontos
    ax.set_xlim(-46.7, -46.4)
    ax.set_ylim(-23.7, -23.4)

    # Estilo do fundo
    ax.set_facecolor('white')  # Mudar fundo para branco
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(True)
    ax.spines['bottom'].set_visible(True)

    # Adiciona grade
    ax.grid(color='lightgrey', linestyle='--', linewidth=0.5)

# Cria a animação
n_bootstrap = 10  # Número de reamostragens bootstrap
ani = FuncAnimation(fig, update, frames=n_bootstrap, repeat=False)

# Salvando a animação como GIF usando PillowWriter
ani.save("bootstrap_vendedores_ajustado.gif", writer=PillowWriter(fps=2))
