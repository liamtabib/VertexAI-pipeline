---
title: Product Dashboard
---

<style>
.summary-content p {
  margin-bottom: 1rem;
}
.summary-content p:last-child {
  margin-bottom: 0;
}
.summary-content {
  white-space: pre-line;
  line-height: 1.6;
}
</style>

```sql latest_summary
SELECT * FROM latest_summary ORDER BY run_ts DESC LIMIT 1
```

```sql data_end_date
SELECT * FROM data_end_date
```

```sql mau_data
SELECT month, mau FROM mau ORDER BY month
```

```sql retention_data
SELECT * FROM retention
```

```sql country_data
SELECT * FROM users_by_country
```

```sql country_increases_data
SELECT * FROM country_increases
```

```sql country_decreases_data
SELECT * FROM country_decreases
```

```sql platform_data
SELECT * FROM platform_share
```

```sql funnel_data
WITH funnel_with_percentages AS (
  SELECT 
    step,
    step_name,
    sessions,
    CASE 
      WHEN step = 1 THEN 1.0
      ELSE ROUND(sessions / FIRST_VALUE(sessions) OVER (ORDER BY step), 3)
    END AS percentage
  FROM funnel
)
SELECT step, step_name, sessions, percentage
FROM funnel_with_percentages
ORDER BY step
```

```sql kpi_data
SELECT * FROM kpi_metrics
```


<div class="grid grid-cols-3 gap-4 mb-8">

<BigValue 
    data={kpi_data} 
    value=last_updated_date
    title="Data last updated"
/>

<BigValue 
    data={kpi_data} 
    value=mau_30_days
    title="MAU Last 30 Days"
    fmt='#,##0'
/>

<BigValue 
    data={kpi_data} 
    value=purchase_conversion_rate
    title="Purchase Conversion last 30 days"
    fmt='#,##0.0%'
/>

</div>


<Grid cols=2 gapSize="lg">
  <BarChart 
    data={mau_data} 
    x=month 
    y=mau 
    title="Monthly Active Users"
    echartsOptions={{
      yAxis: {
        inverse: false
      },
      xAxis: {
        type: 'time'
      },
      series: [{
        smooth: true
      }]
    }}
  />

  <LineChart 
    data={retention_data}
    x=age_month
    y=retention_rate
    series=cohort_label
    yFmt=".0%"
    yMax=1
    title="Monthly Cohort Retention"
    echartsOptions={{
      xAxis: {
        max: 4
      }
    }}
  />
</Grid>


<AreaMap 
  data={country_data}
  geoJsonUrl="https://raw.githubusercontent.com/holtzy/D3-graph-gallery/master/DATA/world.geojson"
  areaCol=country
  geoId=name
  value=users
  title="Users by Country"
  height=420
  colorPalette={["#ce93d8", "#ba68c8", "#ab47bc", "#9c27b0", "#8e24aa", "#7b1fa2", "#6a1b9a", "#4a148c"]}
  legend=false
/>


<Grid cols=2 gapSize="lg">
  <DataTable 
    data={country_increases_data}
    title="Top 3 Increases (Last 30 Days)"
  >
    <Column id="country" title="Country" />
    <Column id="increase_number" title="User Increase" />
    <Column id="increase_percentage" title="% Increase" fmt=".1%" />
  </DataTable>
  
  <DataTable 
    data={country_decreases_data}
    title="Top 3 Decreases (Last 30 Days)"
  >
    <Column id="country" title="Country" />
    <Column id="decrease_number" title="User Decrease" />
    <Column id="decrease_percentage" title="% Decrease" fmt=".1%" />
  </DataTable>
</Grid>


<Grid cols=2 gapSize="lg">
  <BarChart 
    data={platform_data}
    x=platform
    y=share
    yFmt="0%"
    swapXY=true
    stack="normalize"
    title="Users by Platform"
  />

  <FunnelChart 
    data={funnel_data} 
    nameCol="step_name" 
    valueCol="percentage" 
    valueFmt="0.0%"
    title="Shopping Funnel (Latest Full Month)" 
  />
</Grid>



{#if latest_summary.length > 0}
<div class="bg-blue-30 border border-blue-220 rounded-lg p-2 mb-3">
  <h3 class="text-lg font-medium text-blue-90 mb-2">AI Highlights:</h3>
  <div class="text-blue-800 summary-content">{@html latest_summary[0].text}</div>
 
</div>
{/if}

This dashboard and the LLM summarization is powered by [Google Cloud](https://cloud.google.com/), [Vertex AI](https://cloud.google.com/vertex-ai), and [Evidence](https://evidence.dev/). You can find the code on [GitHub](https://github.com/liamtabib/VertexAI-pipeline). *Made by [Liam](https://www.linkedin.com/in/liamtabibzadeh/)*.