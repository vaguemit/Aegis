import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { Maximize2, ZoomIn, ZoomOut, Layers, RefreshCw } from 'lucide-react';

export default function NetworkGraphView({
  graphData,
  activeAttackPath,
  mitigatedAttackPath,
  onSelectNode,
  selectedNodeId,
}) {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  const [layoutName, setLayoutName] = useState('cose');

  // Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Convert nodes to Cytoscape format
    const cyNodes = graphData.nodes.map((n) => {
      let nodeColor = '#475569'; // Default Slate
      let borderColor = '#334155';
      let nodeShape = 'ellipse';

      if (n.entity_type === 'DomainController' || n.entity_type === 'Domain') {
        nodeShape = 'hexagon';
        nodeColor = '#8B5CF6'; // Purple
      } else if (n.entity_type === 'Server') {
        nodeShape = 'round-rectangle';
        nodeColor = '#0284C7'; // Blue
      } else if (n.entity_type === 'Computer') {
        nodeShape = 'rectangle';
        nodeColor = '#3B82F6';
      } else if (n.entity_type === 'User') {
        nodeShape = 'ellipse';
        nodeColor = '#10B981'; // Green
      }

      if (n.is_owned) {
        nodeColor = '#06B6D4'; // Cyan Initial Foothold
        borderColor = '#38BDF8';
      }
      if (n.is_vulnerable) {
        borderColor = '#F59E0B'; // Amber CVE
      }
      if (n.is_target || n.is_high_value) {
        nodeColor = '#EC4899'; // Crown Jewel Pink/Rose
        borderColor = '#F43F5E';
      }

      return {
        data: {
          id: n.id,
          label: n.name,
          index: n.index,
          entity_type: n.entity_type,
          is_vulnerable: n.is_vulnerable,
          is_high_value: n.is_high_value,
          is_owned: n.is_owned,
          is_target: n.is_target,
          rawNode: n,
          color: nodeColor,
          borderColor: borderColor,
          shape: nodeShape,
        },
      };
    });

    // Convert edges to Cytoscape format
    const cyEdges = graphData.edges.map((e) => {
      let edgeColor = '#334155';
      let lineStyle = 'solid';

      if (e.edge_type === 'Open') {
        edgeColor = '#F59E0B';
        lineStyle = 'dashed';
      } else if (e.edge_type === 'AdminTo') {
        edgeColor = '#EF4444';
      } else if (e.edge_type === 'CanRDP' || e.edge_type === 'ExecuteDCOM') {
        edgeColor = '#38BDF8';
      } else if (e.edge_type === 'MemberOf') {
        edgeColor = '#10B981';
      }

      return {
        data: {
          id: e.id,
          source: e.source,
          target: e.target,
          edge_type: e.edge_type,
          color: edgeColor,
          lineStyle: lineStyle,
        },
      };
    });

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#F3F4F6',
            'font-size': '10px',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 4,
            'width': 26,
            'height': 26,
            'shape': 'data(shape)',
            'border-width': 2,
            'border-color': 'data(borderColor)',
            'transition-property': 'background-color, border-color, width, height',
            'transition-duration': '0.2s',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'line-style': 'data(lineStyle)',
            'opacity': 0.6,
            'arrow-scale': 0.8,
          },
        },
        {
          selector: ':selected',
          style: {
            'border-width': 4,
            'border-color': '#38BDF8',
            'box-shadow': '0 0 15px #38BDF8',
          },
        },
      ],
      layout: {
        name: layoutName,
        animate: false,
        randomize: false,
        nodeDimensionsIncludeLabels: true,
        fit: true,
        padding: 40,
      },
    });

    // Node click handler
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      onSelectNode(node.data('rawNode'));
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData, layoutName]);

  // Highlight Attack Paths (Active vs Mitigated)
  useEffect(() => {
    if (!cyRef.current || !graphData) return;
    const cy = cyRef.current;

    // Reset styles
    cy.elements().removeClass('attack-highlight attack-mitigated path-node');
    cy.elements().style({
      'opacity': 0.6,
    });

    if (activeAttackPath && activeAttackPath.nodes && activeAttackPath.nodes.length > 1) {
      const pathNodeIds = activeAttackPath.nodes.map((idx) => `n_${idx}`);

      // Highlight path nodes
      pathNodeIds.forEach((nodeId) => {
        const node = cy.getElementById(nodeId);
        if (node) {
          node.style({
            'opacity': 1.0,
            'border-width': 4,
            'border-color': '#F43F5E',
            'width': 34,
            'height': 34,
          });
        }
      });

      // Highlight path edges
      for (let i = 0; i < pathNodeIds.length - 1; i++) {
        const src = pathNodeIds[i];
        const dst = pathNodeIds[i + 1];
        const edges = cy.edges(`[source = "${src}"][target = "${dst}"]`);
        if (edges.length > 0) {
          edges.style({
            'width': 4,
            'line-color': '#F43F5E',
            'target-arrow-color': '#F43F5E',
            'opacity': 1.0,
            'arrow-scale': 1.4,
            'z-index': 999,
          });
        }
      }
    } else {
      // Restore normal opacity
      cy.elements().style({ 'opacity': 0.8 });
    }
  }, [activeAttackPath, graphData]);

  const handleFit = () => cyRef.current && cyRef.current.fit(null, 40);
  const handleZoomIn = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      {/* Cytoscape DOM Mount */}
      <div id="cy-container" ref={containerRef} />

      {/* Floating Canvas Controls */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '16px',
          right: '16px',
          padding: '6px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          zIndex: 10,
        }}
      >
        <button className="btn-cyber btn-outline" onClick={handleFit} title="Fit to Screen" style={{ padding: '8px' }}>
          <Maximize2 size={16} />
        </button>
        <button className="btn-cyber btn-outline" onClick={handleZoomIn} title="Zoom In" style={{ padding: '8px' }}>
          <ZoomIn size={16} />
        </button>
        <button className="btn-cyber btn-outline" onClick={handleZoomOut} title="Zoom Out" style={{ padding: '8px' }}>
          <ZoomOut size={16} />
        </button>
        <button
          className="btn-cyber btn-outline"
          onClick={() => setLayoutName(layoutName === 'cose' ? 'breadthfirst' : (layoutName === 'breadthfirst' ? 'concentric' : 'cose'))}
          title={`Switch Layout (Current: ${layoutName})`}
          style={{ padding: '8px' }}
        >
          <Layers size={16} />
        </button>
      </div>

      {/* Graph Legend Overlay */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '16px',
          padding: '10px 14px',
          display: 'flex',
          gap: '12px',
          alignItems: 'center',
          fontSize: '0.75rem',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#06B6D4' }} />
          <span>Foothold (Source)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#EC4899' }} />
          <span>Crown Jewel (Target)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '2px', border: '2px solid #F59E0B' }} />
          <span>Vulnerable (CVE)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '12px', height: '3px', background: '#F43F5E' }} />
          <span>Predicted Attack Hop</span>
        </div>
      </div>
    </div>
  );
}
