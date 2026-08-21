import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import {
  Maximize2,
  ZoomIn,
  ZoomOut,
  Layers,
  RefreshCw,
  Target,
  Shield,
  Activity,
  Server,
  Laptop,
  User,
  Info,
  Compass,
  Grid,
  GitBranch,
} from 'lucide-react';

export default function NetworkGraphView({
  graphData,
  activeAttackPath,
  mitigatedAttackPath,
  onSelectNode,
  selectedNodeId,
}) {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  const [layoutName, setLayoutName] = useState('tiered');
  const [hoveredNode, setHoveredNode] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  // 1. Initialize and update Cytoscape instance
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Convert nodes to Cytoscape format
    const cyNodes = graphData.nodes.map((n) => {
      let nodeColor = '#334155';
      let borderColor = '#475569';
      let nodeShape = 'ellipse';
      let tierLevel = 3; // default user / workstation
      let nodeSize = 32;

      const isDC = n.entity_type === 'DomainController' || n.name.toLowerCase().includes('dc') || n.name.toLowerCase().includes('domain');
      const isServer = n.entity_type === 'Server' || n.name.toLowerCase().includes('server') || n.name.toLowerCase().includes('database') || n.name.toLowerCase().includes('sql') || n.name.toLowerCase().includes('web') || n.name.toLowerCase().includes('share');
      const isWorkstation = n.entity_type === 'Computer' || n.name.toLowerCase().includes('workstation') || n.name.toLowerCase().includes('laptop') || n.name.toLowerCase().includes('pc');
      const isUser = n.entity_type === 'User';

      if (isDC) {
        nodeShape = 'hexagon';
        nodeColor = '#7C3AED'; // Deep Violet
        borderColor = '#A78BFA';
        tierLevel = 1;
        nodeSize = 44;
      } else if (isServer) {
        nodeShape = 'round-rectangle';
        nodeColor = '#0284C7'; // Blue
        borderColor = '#38BDF8';
        tierLevel = 2;
        nodeSize = 38;
      } else if (isWorkstation) {
        nodeShape = 'rectangle';
        nodeColor = '#2563EB'; // Royal Blue
        borderColor = '#60A5FA';
        tierLevel = 4;
        nodeSize = 32;
      } else if (isUser) {
        nodeShape = 'ellipse';
        nodeColor = '#059669'; // Emerald
        borderColor = '#34D399';
        tierLevel = 5;
        nodeSize = 28;
      }

      if (n.is_owned) {
        nodeColor = '#06B6D4'; // Cyan Initial Breach Foothold
        borderColor = '#67E8F9';
        nodeSize = Math.max(nodeSize, 38);
      }
      if (n.is_vulnerable) {
        borderColor = '#F59E0B'; // Amber CVE
      }
      if (n.is_target || n.is_high_value) {
        nodeColor = '#E11D48'; // Rose Crown Jewel Target
        borderColor = '#FDA4AF';
        nodeSize = Math.max(nodeSize, 44);
      }

      // Display Name Formatting
      let displayName = n.name;
      if (displayName.length > 22) {
        displayName = displayName.substring(0, 20) + '...';
      }

      return {
        data: {
          id: n.id,
          label: displayName,
          fullLabel: n.name,
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
          size: nodeSize,
          tierLevel: tierLevel,
        },
      };
    });

    // Convert edges to Cytoscape format
    const cyEdges = graphData.edges.map((e) => {
      let edgeColor = '#22222E';
      let lineStyle = 'solid';
      let edgeWidth = 1.5;

      if (e.edge_type === 'Open') {
        edgeColor = '#F59E0B';
        lineStyle = 'dashed';
        edgeWidth = 2;
      } else if (e.edge_type === 'AdminTo') {
        edgeColor = '#EF4444';
        edgeWidth = 2;
      } else if (e.edge_type === 'CanRDP' || e.edge_type === 'ExecuteDCOM') {
        edgeColor = '#38BDF8';
        edgeWidth = 1.8;
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
          width: edgeWidth,
        },
      };
    });

    // Cytoscape Core Configuration
    const cy = cytoscape({
      container: containerRef.current,
      elements: [...cyNodes, ...cyEdges],
      boxSelectionEnabled: false,
      autounselectify: false,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'color': '#FFFFFF',
            'font-size': '10px',
            'font-weight': '600',
            'font-family': 'Inter, sans-serif',
            'text-valign': 'bottom',
            'text-margin-y': 5,
            'text-background-color': 'rgba(8, 8, 12, 0.85)',
            'text-background-opacity': 0.85,
            'text-background-padding': 3,
            'text-background-shape': 'roundrectangle',
            'width': 'data(size)',
            'height': 'data(size)',
            'shape': 'data(shape)',
            'border-width': 2,
            'border-color': 'data(borderColor)',
            'transition-property': 'background-color, border-color, width, height, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.9,
            'curve-style': 'bezier',
            'line-style': 'data(lineStyle)',
            'opacity': 0.45,
            'transition-property': 'line-color, target-arrow-color, width, opacity',
            'transition-duration': '0.15s',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#FFFFFF',
            'border-opacity': 1,
            'shadow-blur': 15,
            'shadow-color': '#FFFFFF',
            'shadow-opacity': 0.5,
          },
        },
        {
          selector: '.faded',
          style: {
            'opacity': 0.12,
          },
        },
        {
          selector: '.highlighted-neighbor',
          style: {
            'opacity': 1,
            'border-width': 3,
            'border-color': '#38BDF8',
          },
        },
        {
          selector: '.highlighted-edge',
          style: {
            'opacity': 1,
            'width': 3,
            'line-color': '#38BDF8',
            'target-arrow-color': '#38BDF8',
          },
        },
        {
          selector: '.attack-path-node',
          style: {
            'border-width': 4,
            'border-color': '#F43F5E',
            'shadow-blur': 20,
            'shadow-color': '#F43F5E',
            'shadow-opacity': 0.8,
            'opacity': 1,
          },
        },
        {
          selector: '.attack-path-edge',
          style: {
            'width': 4,
            'line-color': '#F43F5E',
            'target-arrow-color': '#F43F5E',
            'opacity': 1,
            'line-style': 'solid',
            'arrow-scale': 1.3,
            'shadow-blur': 10,
            'shadow-color': '#F43F5E',
            'shadow-opacity': 0.7,
          },
        },
      ],
    });

    cyRef.current = cy;

    // Node Interaction Events
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const rawNode = node.data('rawNode');
      if (onSelectNode) onSelectNode(rawNode);

      // Focus Mode: Highlight neighborhood and fade rest
      cy.elements().removeClass('faded highlighted-neighbor highlighted-edge');
      const neighborhood = node.neighborhood().add(node);
      cy.elements().difference(neighborhood).addClass('faded');
      node.neighborhood('node').addClass('highlighted-neighbor');
      node.neighborhood('edge').addClass('highlighted-edge');
    });

    // Reset Focus on Canvas Click
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        cy.elements().removeClass('faded highlighted-neighbor highlighted-edge');
      }
    });

    // Tooltip Hover Events
    cy.on('mouseover', 'node', (evt) => {
      const node = evt.target;
      const rawNode = node.data('rawNode');
      const renderedPos = node.renderedPosition();
      setHoveredNode(rawNode);
      setTooltipPos({ x: renderedPos.x, y: renderedPos.y });
    });

    cy.on('mouseout', 'node', () => {
      setHoveredNode(null);
    });

    applyLayout(cy, layoutName);

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  // Apply layout algorithm
  const applyLayout = (cyInstance, type) => {
    if (!cyInstance) return;

    let layoutConfig = {};

    if (type === 'tiered') {
      // Clean Hierarchical Tiered Dagre/Breadthfirst layout
      layoutConfig = {
        name: 'breadthfirst',
        directed: true,
        padding: 40,
        spacingFactor: 1.25,
        avoidOverlap: true,
        circle: false,
        roots: cyInstance.nodes('[tierLevel = 1]'), // DC roots at top
      };
    } else if (type === 'concentric') {
      // Concentric Security Rings (Crown Jewels in center)
      layoutConfig = {
        name: 'concentric',
        concentric: (node) => 6 - node.data('tierLevel'),
        levelWidth: () => 1,
        padding: 35,
        avoidOverlap: true,
        spacingFactor: 1.15,
      };
    } else if (type === 'grid') {
      // Subnet Grid Matrix
      layoutConfig = {
        name: 'grid',
        padding: 40,
        avoidOverlap: true,
        rows: Math.ceil(Math.sqrt(cyInstance.nodes().length)),
      };
    } else {
      // Organic Spring Cose layout
      layoutConfig = {
        name: 'cose',
        idealEdgeLength: 60,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 35,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 300,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      };
    }

    const layout = cyInstance.layout(layoutConfig);
    layout.run();
  };

  const handleSwitchLayout = (type) => {
    setLayoutName(type);
    applyLayout(cyRef.current, type);
  };

  // Highlight Attack Paths
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    cy.elements().removeClass('attack-path-node attack-path-edge');

    if (activeAttackPath && activeAttackPath.nodes) {
      activeAttackPath.nodes.forEach((nodeIdx) => {
        cy.nodes(`[index = ${nodeIdx}]`).addClass('attack-path-node');
      });

      for (let i = 0; i < activeAttackPath.nodes.length - 1; i++) {
        const u = activeAttackPath.nodes[i];
        const v = activeAttackPath.nodes[i + 1];
        cy.edges(`[source = "node_${u}"][target = "node_${v}"]`).addClass('attack-path-edge');
      }
    }
  }, [activeAttackPath]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', overflow: 'hidden' }}>
      {/* Cytoscape Graph Canvas */}
      <div ref={containerRef} id="cy-container" />

      {/* Floating Canvas Control Toolbar */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          padding: '6px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          background: 'rgba(9, 9, 13, 0.92)',
          border: '1px solid #22222E',
          borderRadius: '8px',
          zIndex: 10,
        }}
      >
        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('tiered')}
          style={{
            padding: '5px 10px',
            fontSize: '0.74rem',
            background: layoutName === 'tiered' ? '#FFFFFF' : '#14141C',
            color: layoutName === 'tiered' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Hierarchical Tiered Architecture (DCs → Servers → Endpoints)"
        >
          <GitBranch size={13} /> Tiered View
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('concentric')}
          style={{
            padding: '5px 10px',
            fontSize: '0.74rem',
            background: layoutName === 'concentric' ? '#FFFFFF' : '#14141C',
            color: layoutName === 'concentric' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Concentric Security Rings (Crown Jewels in Center)"
        >
          <Target size={13} /> Security Rings
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('grid')}
          style={{
            padding: '5px 10px',
            fontSize: '0.74rem',
            background: layoutName === 'grid' ? '#FFFFFF' : '#14141C',
            color: layoutName === 'grid' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Subnet Matrix Grid"
        >
          <Grid size={13} /> Grid View
        </button>

        <button
          className="btn-cyber"
          onClick={() => handleSwitchLayout('cose')}
          style={{
            padding: '5px 10px',
            fontSize: '0.74rem',
            background: layoutName === 'cose' ? '#FFFFFF' : '#14141C',
            color: layoutName === 'cose' ? '#000000' : 'var(--text-secondary)',
          }}
          title="Organic Force-Directed Spring Layout"
        >
          <Activity size={13} /> Organic View
        </button>

        <div style={{ width: '1px', height: '18px', background: '#2B2B38', margin: '0 4px' }} />

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.fit(null, 40)}
          style={{ padding: '5px 8px' }}
          title="Fit Graph to Screen"
        >
          <Maximize2 size={13} />
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 1.25)}
          style={{ padding: '5px 8px' }}
          title="Zoom In"
        >
          <ZoomIn size={13} />
        </button>

        <button
          className="btn-cyber btn-outline"
          onClick={() => cyRef.current && cyRef.current.zoom(cyRef.current.zoom() * 0.8)}
          style={{ padding: '5px 8px' }}
          title="Zoom Out"
        >
          <ZoomOut size={13} />
        </button>
      </div>

      {/* Floating Topology Legend Banner */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '12px',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          background: 'rgba(9, 9, 13, 0.92)',
          border: '1px solid #22222E',
          borderRadius: '8px',
          fontSize: '0.72rem',
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', background: '#06B6D4', borderRadius: '2px' }} />
          <span>Attacker Foothold</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', background: '#E11D48', borderRadius: '2px' }} />
          <span>Crown Jewel Target</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', background: '#7C3AED', borderRadius: '2px' }} />
          <span>Domain Controller</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', background: '#0284C7', borderRadius: '2px' }} />
          <span>Server</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', background: '#2563EB', borderRadius: '2px' }} />
          <span>Workstation</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{ width: '10px', height: '10px', border: '2px solid #F59E0B', borderRadius: '2px' }} />
          <span>CVE Vulnerable</span>
        </div>
      </div>

      {/* Interactive Floating Node Hover Tooltip */}
      {hoveredNode && (
        <div
          style={{
            position: 'absolute',
            left: `${Math.min(window.innerWidth - 320, tooltipPos.x + 20)}px`,
            top: `${Math.min(window.innerHeight - 180, tooltipPos.y + 20)}px`,
            padding: '10px 14px',
            background: '#0B0B10',
            border: '1px solid #333345',
            borderRadius: '8px',
            boxShadow: '0 15px 35px rgba(0,0,0,0.9)',
            zIndex: 100,
            pointerEvents: 'none',
            minWidth: '220px',
          }}
        >
          <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#FFFFFF', marginBottom: '2px' }}>
            {hoveredNode.name}
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
            Type: {hoveredNode.entity_type} {hoveredNode.os ? `• ${hoveredNode.os}` : ''}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {hoveredNode.is_owned && <span className="badge badge-cyan" style={{ fontSize: '0.62rem' }}>Initial Breach Foothold</span>}
            {hoveredNode.is_target && <span className="badge badge-rose" style={{ fontSize: '0.62rem' }}>Crown Jewel Target</span>}
            {hoveredNode.is_vulnerable && <span className="badge badge-amber" style={{ fontSize: '0.62rem' }}>Unpatched CVE Exploit</span>}
            {hoveredNode.has_spn && <span className="badge badge-purple" style={{ fontSize: '0.62rem' }}>Kerberoastable SPN</span>}
          </div>
        </div>
      )}
    </div>
  );
}
