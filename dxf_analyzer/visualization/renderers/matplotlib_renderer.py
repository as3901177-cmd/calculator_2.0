"""
Matplotlib-based DXF visualization
"""

import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List, Tuple, Optional, Any
from matplotlib.figure import Figure

from ...core.models import DXFObject, ObjectStatus
from ...core.errors import ErrorCollector
from ..styles.color_schemes import get_status_color, get_chain_color
from ..styles.status_colors import STATUS_COLORS
from ...utils.color_utils import fix_white_color
from ...core.config import get_aci_color


class MatplotlibRenderer:
    """Matplotlib-based renderer for DXF visualization"""

    def __init__(self, figsize: Tuple[int, int] = (16, 12)):
        self.figsize = figsize

    def render(
        self,
        doc: Any,
        objects_data: List[DXFObject],
        collector: ErrorCollector,
        show_markers: bool = True,
        font_size_multiplier: float = 1.0,
        use_original_colors: bool = True,
        show_chains: bool = False
    ) -> Tuple[Optional[Figure], Optional[str]]:
        try:
            fig, ax = plt.subplots(figsize=self.figsize)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_xlabel('X (mm)', fontsize=10)
            ax.set_ylabel('Y (mm)', fontsize=10)

            # Generate chain color map
            chain_color_map = {}
            if show_chains:
                chain_color_map = self._generate_chain_colors(objects_data)

            # Collect bounds
            all_x, all_y = [], []

            # Draw objects
            for obj in objects_data:
                color, linewidth, alpha = self._get_object_style(
                    obj, use_original_colors, show_chains, chain_color_map
                )
                self._draw_entity(ax, obj.entity, color, linewidth, alpha, all_x, all_y)

            # Set axis limits
            if all_x and all_y:
                margin = 50
                x_min, x_max = min(all_x), max(all_x)
                y_min, y_max = min(all_y), max(all_y)
                ax.set_xlim(x_min - margin, x_max + margin)
                ax.set_ylim(y_min - margin, y_max + margin)

            # Draw markers
            if show_markers:
                self._draw_markers(
                    ax, objects_data, show_chains,
                    chain_color_map, font_size_multiplier
                )

            # Set title
            title = self._get_title(show_chains, objects_data)
            ax.set_title(title, fontsize=14, weight='bold')

            plt.tight_layout()
            return fig, None

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in visualization: {error_details}")
            return None, str(e)

    def _generate_chain_colors(self, objects_data: List[DXFObject]) -> dict:
        unique_chains = list(set(obj.chain_id for obj in objects_data))
        num_chains = len(unique_chains)
        colors_array = plt.cm.rainbow(np.linspace(0, 1, num_chains))
        return {
            chain_id: colors_array[i]
            for i, chain_id in enumerate(sorted(unique_chains))
        }

    def _get_object_style(
        self, obj: DXFObject, use_original_colors: bool,
        show_chains: bool, chain_color_map: dict
    ) -> Tuple[Any, float, float]:
        if show_chains:
            color = chain_color_map.get(obj.chain_id, 'black')
            linewidth = 1.5
            alpha = 0.8
        elif use_original_colors:
            original_color = get_aci_color(obj.original_color)
            color = fix_white_color(original_color)
            linewidth = 1.0
            alpha = 0.9
        else:
            color = get_status_color(obj.status)
            linewidth = 1.5 if obj.status != ObjectStatus.NORMAL else 1.0
            alpha = 0.7
        return color, linewidth, alpha

    def _draw_entity(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        entity_type = entity.dxftype()
        if entity_type == 'LINE':
            self._draw_line(ax, entity, color, linewidth, alpha, all_x, all_y)
        elif entity_type == 'CIRCLE':
            self._draw_circle(ax, entity, color, linewidth, alpha, all_x, all_y)
        elif entity_type == 'ARC':
            self._draw_arc(ax, entity, color, linewidth, alpha, all_x, all_y)
        elif entity_type in ('LWPOLYLINE', 'POLYLINE'):
            self._draw_polyline(ax, entity, color, linewidth, alpha, all_x, all_y)
        elif entity_type == 'SPLINE':
            self._draw_spline(ax, entity, color, linewidth, alpha, all_x, all_y)
        elif entity_type == 'ELLIPSE':
            self._draw_ellipse(ax, entity, color, linewidth, alpha, all_x, all_y)

    def _draw_line(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        start = entity.dxf.start
        end = entity.dxf.end
        ax.plot([start.x, end.x], [start.y, end.y],
                color=color, linewidth=linewidth, alpha=alpha)
        all_x.extend([start.x, end.x])
        all_y.extend([start.y, end.y])

    def _draw_circle(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        center = entity.dxf.center
        radius = entity.dxf.radius
        circle = plt.Circle((center.x, center.y), radius,
                            fill=False, color=color,
                            linewidth=linewidth, alpha=alpha)
        ax.add_patch(circle)
        all_x.extend([center.x - radius, center.x + radius])
        all_y.extend([center.y - radius, center.y + radius])

    def _draw_arc(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        center = entity.dxf.center
        radius = entity.dxf.radius
        start_angle = entity.dxf.start_angle
        end_angle = entity.dxf.end_angle
        arc = patches.Arc((center.x, center.y), 2*radius, 2*radius,
                          theta1=start_angle, theta2=end_angle,
                          color=color, linewidth=linewidth, alpha=alpha)
        ax.add_patch(arc)
        all_x.append(center.x)
        all_y.append(center.y)

    def _draw_polyline(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        """Рисование POLYLINE/LWPOLYLINE с интерполяцией bulge."""
        entity_type = entity.dxftype()

        if entity_type == 'LWPOLYLINE':
            try:
                points_b = list(entity.get_points('xyb'))
            except Exception:
                return

            if not points_b:
                return

            is_closed = entity.closed
            interpolated_xs = []
            interpolated_ys = []

            # Обрабатываем открытые сегменты
            for i in range(len(points_b) - 1):
                x1, y1, bulge = points_b[i]
                x2, y2, _ = points_b[i + 1]
                seg_x, seg_y = self._interpolate_bulge_segment(x1, y1, x2, y2, bulge)
                interpolated_xs.extend(seg_x)
                interpolated_ys.extend(seg_y)

            # Замыкающий сегмент, если полилиния замкнута
            if is_closed and len(points_b) > 1:
                x1, y1, bulge = points_b[-1]
                x2, y2, _ = points_b[0]
                seg_x, seg_y = self._interpolate_bulge_segment(x1, y1, x2, y2, bulge)
                interpolated_xs.extend(seg_x)
                interpolated_ys.extend(seg_y)

            ax.plot(interpolated_xs, interpolated_ys,
                    color=color, linewidth=linewidth, alpha=alpha)
            all_x.extend(interpolated_xs)
            all_y.extend(interpolated_ys)

        else:  # POLYLINE (3D, без bulge)
            points = list(entity.points())
            xs = [p.x for p in points]
            ys = [p.y for p in points]
            is_closed = entity.is_closed
            if is_closed and len(xs) > 0:
                xs.append(xs[0])
                ys.append(ys[0])
            ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)
            all_x.extend(xs)
            all_y.extend(ys)

    def _interpolate_bulge_segment(self, x1, y1, x2, y2, bulge, num_points=50):
        """
        Аппроксимация дугового сегмента LWPOLYLINE набором точек.
        Возвращает (список_x, список_y).
        """
        if abs(bulge) < 1e-10:
            return [x1, x2], [y1, y2]

        # Длина хорды
        chord = math.hypot(x2 - x1, y2 - y1)
        if chord < 1e-10:
            return [x1], [y1]

        abs_bulge = abs(bulge)
        # sin(half central angle) = 2*|b| / (1 + b^2)
        sin_hca = 2.0 * abs_bulge / (1.0 + abs_bulge * abs_bulge)
        if abs(sin_hca) < 1e-10:
            return [x1, x2], [y1, y2]

        radius = chord / (2.0 * sin_hca)
        central_angle = 4.0 * math.atan(abs_bulge)

        # Угол наклона хорды
        chord_angle = math.atan2(y2 - y1, x2 - x1)
        # Смещение центра дуги относительно середины хорды
        mid_x = (x1 + x2) / 2.0
        mid_y = (y1 + y2) / 2.0
        offset = radius * math.cos(central_angle / 2.0)

        if bulge > 0:
            center_angle_offset = chord_angle + math.pi / 2.0
        else:
            center_angle_offset = chord_angle - math.pi / 2.0

        center_x = mid_x + offset * math.cos(center_angle_offset)
        center_y = mid_y + offset * math.sin(center_angle_offset)

        # Начальный и конечный углы дуги в системе координат центра
        start_angle = math.atan2(y1 - center_y, x1 - center_x)
        end_angle = math.atan2(y2 - center_y, x2 - center_x)

        # Обеспечиваем правильное направление обхода
        if bulge > 0:
            while end_angle < start_angle:
                end_angle += 2 * math.pi
        else:
            while end_angle > start_angle:
                end_angle -= 2 * math.pi

        pts_x, pts_y = [], []
        for i in range(num_points + 1):
            t = i / num_points
            angle = start_angle + t * (end_angle - start_angle)
            pts_x.append(center_x + radius * math.cos(angle))
            pts_y.append(center_y + radius * math.sin(angle))
        return pts_x, pts_y

    def _draw_spline(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        try:
            points = list(entity.flattening(0.01))
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, color=color, linewidth=linewidth, alpha=alpha)
            all_x.extend(xs)
            all_y.extend(ys)
        except Exception:
            pass

    def _draw_ellipse(self, ax, entity, color, linewidth, alpha, all_x, all_y):
        center = entity.dxf.center
        major_axis = entity.dxf.major_axis
        ratio = entity.dxf.ratio
        a = math.hypot(major_axis.x, major_axis.y)
        b = a * ratio
        ellipse = patches.Ellipse((center.x, center.y), 2*a, 2*b,
                                  fill=False, color=color,
                                  linewidth=linewidth, alpha=alpha)
        ax.add_patch(ellipse)
        all_x.append(center.x)
        all_y.append(center.y)

    def _draw_markers(self, ax, objects_data, show_chains,
                     chain_color_map, font_size_multiplier):
        base_font_size = 6 * font_size_multiplier
        for obj in objects_data:
            if obj.center is None:
                continue
            x, y = obj.center
            if show_chains:
                marker_color = chain_color_map.get(obj.chain_id, 'black')
                if isinstance(marker_color, np.ndarray):
                    marker_color = tuple(marker_color)
                label_text = f"C{obj.chain_id}"
                markersize = 6
            else:
                if obj.status == ObjectStatus.ERROR:
                    marker_color = 'red'
                    markersize = 7
                elif obj.status == ObjectStatus.WARNING:
                    marker_color = 'orange'
                    markersize = 6
                else:
                    marker_color = 'blue'
                    markersize = 5
                label_text = str(obj.num)

            ax.plot(x, y,
                    marker='o',
                    color=marker_color,
                    markersize=markersize,
                    alpha=0.9,
                    markeredgecolor='white',
                    markeredgewidth=1.0,
                    zorder=100)
            ax.text(x, y, f" {label_text}",
                    fontsize=base_font_size,
                    color=marker_color,
                    weight='bold',
                    ha='left',
                    va='center',
                    zorder=101,
                    bbox=dict(
                        boxstyle='round,pad=0.3',
                        facecolor='white',
                        alpha=0.9,
                        edgecolor=marker_color,
                        linewidth=1.5
                    ))

    def _get_title(self, show_chains, objects_data):
        if show_chains:
            num_chains = len(set(obj.chain_id for obj in objects_data))
            return f"Chain Visualization ({num_chains} chains)"
        else:
            return "DXF Drawing Visualization"


# Legacy function for backward compatibility
def visualize_dxf_with_status_indicators(
    doc: Any,
    objects_data: List[DXFObject],
    collector: ErrorCollector,
    show_markers: bool = True,
    font_size_multiplier: float = 1.0,
    use_original_colors: bool = True,
    show_chains: bool = False
) -> Tuple[Optional[Figure], Optional[str]]:
    renderer = MatplotlibRenderer()
    return renderer.render(
        doc, objects_data, collector, show_markers,
        font_size_multiplier, use_original_colors, show_chains
    )
