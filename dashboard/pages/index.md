---
title: Product Dashboard
---

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
    title="Purchase Conversion (30d)"
    fmt='#,##0.0%'
/>

</div>

<p class="text-sm text-gray-600 mb-6">
As of <strong>{data_end_date[0].data_end_date}</strong> — monthly charts exclude the current month; funnel uses the latest full month.
</p>

## Monthly Activity & Retention

<Grid cols=2 gapSize="lg">
  <AreaChart 
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

## Geographic Distribution & Trends

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

## Country Growth Trends

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

## Platform Analysis & Conversion Funnel

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



## Build Your Own Insights.
This dashboard is powered by [Google Cloud](https://cloud.google.com/), [Vertex AI](https://cloud.google.com/vertex-ai), and [Evidence](https://evidence.dev/). You can find the code for this dashboard on [GitHub](https://github.com/mehd-io/pypi-duck-flow).


*Made with ❤️ by 🧢 [Liam](https://www.linkedin.com/in/liamtabibzadeh/)*