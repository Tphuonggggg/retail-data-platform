"""Deterministic PBIP/PBIR authoring from the Owner's inspected PBIX metadata.

Does not overwrite the PBIX, connect to PostgreSQL, or run dbt/ingestion.
Generated metadata still requires Desktop refresh, DAX and rendered validation.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from uuid import uuid5, NAMESPACE_URL
import zipfile

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'powerbi'
PROJECT=HERE/'RetailSalesAnalytics'
REPORT=PROJECT/'RetailSalesAnalytics.Report'
MODEL=PROJECT/'RetailSalesAnalytics.SemanticModel'
PIN='c825b18e-fc62-4cf1-8837-b37b4c9f9668'
F='Invoice Lines'; D='Date'; P='Product'; B='Buyer'; BT='Bill-to'; IH='Invoices'; OH='Orders'


def uid(label):return str(uuid5(NAMESPACE_URL,'retail-sales-01/'+label))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def measures():
    output=[]
    def add(name,expression,folder='Sales',fmt='#,0.00',description=None):
        output.append({'name':name,'expression':expression,'formatString':fmt,
                       'displayFolder':folder,'description':description or name,
                       'lineageTag':uid('measure/'+name)})
    add('Total Sales Before Tax',"CALCULATE(SUM('Invoice Lines'[invoiced_sales_before_tax]),'Invoice Lines'[is_sales_eligible]=TRUE())",description='S05: invoiced sales before tax, InvoiceDate; not recognized revenue. Eligible WARNING rows retained.')
    for name,col in [('Total Tax','tax_amount'),('Total Amount Including Tax','invoice_amount_including_tax'),('Units Sold','quantity')]:
        add(name,f"CALCULATE(SUM('Invoice Lines'[{col}]),'Invoice Lines'[is_sales_eligible]=TRUE())",fmt='#,0' if name=='Units Sold' else '#,0.00')
    add('Eligible Invoice Lines',"CALCULATE(COUNTROWS('Invoice Lines'),'Invoice Lines'[is_sales_eligible]=TRUE())",fmt='#,0')
    add('Invoice Count',"""VAR BaseCount=CALCULATE(COUNTROWS(Invoices),Invoices[is_sales_eligible]=TRUE())
RETURN IF(ISCROSSFILTERED(Product),
 CALCULATE(COUNTROWS(Invoices),Invoices[is_sales_eligible]=TRUE(),
 TREATAS(CALCULATETABLE(VALUES('Invoice Lines'[source_invoice_id]),'Invoice Lines'[is_sales_eligible]=TRUE()),Invoices[source_invoice_id])),BaseCount)""",fmt='#,0',description='S02: eligible invoice-header population. Product filtering uses invoice ID semijoin, never summed product distinct counts.')
    add('Order Count',"CALCULATE(COUNTROWS(Orders),Orders[is_order_eligible]=TRUE())",fmt='#,0',description='S01: Orders/OrderDate, including uninvoiced orders; intentionally not product-filtered.')
    add('Average Invoice Value','DIVIDE([Total Sales Before Tax],[Invoice Count])',description='S06: recomputed ratio of totals in the same context; not AOV.')
    add('Sales per Unit','DIVIDE([Total Sales Before Tax],[Units Sold])',description='Source quantity basis; not standardized packaging or piece price.')
    for label,base in [('Sales','Total Sales Before Tax'),('Invoice Count','Invoice Count'),('AIV','Average Invoice Value')]:
        add(label+' Previous Year Comparable Period',f"""VAR PreviousDates=SELECTCOLUMNS(VALUES('Date'[calendar_date]),"PriorDate",EDATE('Date'[calendar_date],-12))
RETURN IF(HASONEVALUE('Date'[calendar_year]),CALCULATE([{base}],REMOVEFILTERS('Date'),TREATAS(PreviousDates,'Date'[calendar_date])))""",'Time intelligence',description='Only one selected calendar year. Same selected dates shifted 12 months; leap day maps to prior Feb 28. Other filters retained.')
        add(label+' YoY %',f'DIVIDE([{base}]-[{label} Previous Year Comparable Period],[{label} Previous Year Comparable Period])','Time intelligence','0.00%;-0.00%;0.00%')
    add('Sales Previous Period',"IF(HASONEVALUE('Date'[Year Month]),CALCULATE([Total Sales Before Tax],REMOVEFILTERS('Date'),DATEADD('Date'[calendar_date],-1,MONTH)))",'Time intelligence',description='Previous month only in a single year-month context; BLANK at multi-month totals.')
    add('Sales MoM %','DIVIDE([Total Sales Before Tax]-[Sales Previous Period],[Sales Previous Period])','Time intelligence','0.00%;-0.00%;0.00%')
    add('Sales YTD',"VAR Cutoff=MAX('Date'[calendar_date]) RETURN CALCULATE([Total Sales Before Tax],REMOVEFILTERS('Date'),DATESBETWEEN('Date'[calendar_date],DATE(YEAR(Cutoff),1,1),Cutoff))",'Time intelligence')
    add('Prior Year Comparable YTD',"VAR Cutoff=MAX('Date'[calendar_date]) VAR Prior=EDATE(Cutoff,-12) RETURN CALCULATE([Total Sales Before Tax],REMOVEFILTERS('Date'),DATESBETWEEN('Date'[calendar_date],DATE(YEAR(Prior),1,1),Prior))",'Time intelligence')
    add('YTD YoY %','DIVIDE([Sales YTD]-[Prior Year Comparable YTD],[Prior Year Comparable YTD])','Time intelligence','0.00%;-0.00%;0.00%')
    add('Volume Contribution',"IF(NOT ISBLANK([Invoice Count Previous Year Comparable Period]),([Invoice Count]-[Invoice Count Previous Year Comparable Period])*[AIV Previous Year Comparable Period])",'Decomposition')
    add('AIV Contribution',"IF(NOT ISBLANK([Invoice Count Previous Year Comparable Period]),([Average Invoice Value]-[AIV Previous Year Comparable Period])*[Invoice Count Previous Year Comparable Period])",'Decomposition')
    add('Interaction Contribution',"IF(NOT ISBLANK([Invoice Count Previous Year Comparable Period]),([Invoice Count]-[Invoice Count Previous Year Comparable Period])*([Average Invoice Value]-[AIV Previous Year Comparable Period]))",'Decomposition')
    add('Sales Change Contribution',"SWITCH(SELECTEDVALUE(Decomposition[Component]),\"Invoice volume\",[Volume Contribution],\"AIV\",[AIV Contribution],\"Interaction\",[Interaction Contribution])",'Decomposition',description='Exact three-term delta: deltaN*A0 + N0*deltaA + deltaN*deltaA. Arithmetic, not causality.')
    add('Performance Narrative',"IF(ISBLANK([Sales YoY %]),\"Select one calendar year. 2016 covers January–May only.\",\"Sales \"&FORMAT([Sales YoY %],\"+0.00%;-0.00%\")&\" | invoices \"&FORMAT([Invoice Count YoY %],\"+0.00%;-0.00%\")&\" | AIV \"&FORMAT([AIV YoY %],\"+0.00%;-0.00%\")&\" versus equivalent prior-year dates.\")",'Narratives','')
    add('Product Sales','[Total Sales Before Tax]','Products')
    add('Product Units','[Units Sold]','Products','#,0')
    add('Product Sales per Unit','[Sales per Unit]','Products')
    add('Product Sales Share %',"DIVIDE([Product Sales],CALCULATE([Product Sales],ALLSELECTED(Product)))",'Products','0.00%')
    for suffix,base in [('Sales','Product Sales'),('Units','Product Units')]:
        add('Product Rank by '+suffix,f"""VAR ThisId=SELECTEDVALUE(Product[source_stock_item_id]) VAR ThisValue=[{base}]
VAR Population=FILTER(ADDCOLUMNS(ALLSELECTED(Product),"@Value",[{base}],"@Lines",[Eligible Invoice Lines]),[@Lines]>0)
RETURN IF(HASONEVALUE(Product[source_stock_item_id])&&NOT ISBLANK(ThisValue),1+COUNTROWS(FILTER(Population,[@Value]>ThisValue||([@Value]=ThisValue&&Product[source_stock_item_id]<ThisId))))""",'Products','#,0',description='Selected product population; deterministic SKU ID tie-break.')
    add('Product Cumulative Sales',"""VAR ThisId=SELECTEDVALUE(Product[source_stock_item_id]) VAR ThisSales=[Product Sales]
VAR Population=ADDCOLUMNS(ALLSELECTED(Product),"@Sales",[Product Sales])
RETURN IF(HASONEVALUE(Product[source_stock_item_id]),SUMX(FILTER(Population,[@Sales]>ThisSales||([@Sales]=ThisSales&&Product[source_stock_item_id]<=ThisId)),[@Sales]))""",'Products')
    add('Product Cumulative Sales %',"DIVIDE([Product Cumulative Sales],CALCULATE([Product Sales],ALLSELECTED(Product)))",'Products','0.0%')
    add('Pareto Threshold','0.8','Products','0%')
    add('Distinct Active Products',"COUNTROWS(FILTER(VALUES(Product[source_stock_item_id]),[Eligible Invoice Lines]>0))",'Products','#,0')
    add('Top 20% SKU Sales Share',"VAR Population=FILTER(ADDCOLUMNS(ALLSELECTED(Product),\"@Sales\",[Product Sales],\"@Lines\",[Eligible Invoice Lines]),[@Lines]>0) VAR N=ROUNDUP(COUNTROWS(Population)*0.2,0) RETURN DIVIDE(SUMX(TOPN(N,Population,[@Sales],DESC,Product[source_stock_item_id],ASC),[@Sales]),SUMX(Population,[@Sales]))",'Products','0.00%')
    add('SKUs for 80% Sales',"""VAR Population=FILTER(ADDCOLUMNS(ALLSELECTED(Product),"@Sales",[Product Sales],"@Lines",[Eligible Invoice Lines]),[@Lines]>0)
VAR TotalSales=SUMX(Population,[@Sales])
RETURN IF(TotalSales>0,1+COUNTROWS(FILTER(Population,VAR S=[@Sales] VAR K=Product[source_stock_item_id]
VAR Cumulative=SUMX(FILTER(Population,[@Sales]>S||([@Sales]=S&&Product[source_stock_item_id]<=K)),[@Sales]) RETURN Cumulative<TotalSales*0.8)))""",'Products','#,0')
    add('Selected Top N','SELECTEDVALUE(\'Top N\'[Value],10)','Parameters','#,0')
    add('Top N Ranking Overlap',"VAR Population=FILTER(ADDCOLUMNS(ALLSELECTED(Product),\"@Sales\",[Product Sales],\"@Units\",[Product Units],\"@Lines\",[Eligible Invoice Lines]),[@Lines]>0) VAR N=[Selected Top N] VAR A=SELECTCOLUMNS(TOPN(N,Population,[@Sales],DESC,Product[source_stock_item_id],ASC),\"ID\",Product[source_stock_item_id]) VAR B=SELECTCOLUMNS(TOPN(N,Population,[@Units],DESC,Product[source_stock_item_id],ASC),\"ID\",Product[source_stock_item_id]) RETURN COUNTROWS(INTERSECT(A,B))",'Products','#,0')
    for suffix in ('Sales','Units'):
        add('Top N Product '+suffix,f'IF([Product Rank by {suffix}]<=[Selected Top N],[Product {suffix}])','Products','#,0' if suffix=='Units' else '#,0.00')
    add('Product Active Months',"COUNTROWS(FILTER(VALUES('Date'[Year Month]),[Eligible Invoice Lines]>0))",'Products','#,0')
    add('Product Lifetime Rank',"CALCULATE([Product Rank by Sales],REMOVEFILTERS('Date'))",'Products','#,0')
    add('Comparable-Period Product Rank',"VAR Cutoff=CALCULATE(MAX('Date'[calendar_date]),REMOVEFILTERS('Date')) RETURN CALCULATE([Product Rank by Sales],REMOVEFILTERS('Date'),DATESBETWEEN('Date'[calendar_date],DATE(YEAR(Cutoff),1,1),Cutoff))",'Products','#,0')
    add('Product Rank Change','[Product Lifetime Rank]-[Comparable-Period Product Rank]','Products','#,0')
    add('Product Rank by Selected Basis','IF(SELECTEDVALUE(\'Ranking Basis\'[Basis],"Sales")="Units",[Product Rank by Units],[Product Rank by Sales])','Products','#,0')
    for role,table,other in [('Buyer','Buyer','Bill-to'),('Bill-to','Bill-to','Buyer')]:
        add(role+' Sales',f"CALCULATE([Total Sales Before Tax],REMOVEFILTERS('{other}'))",'Attribution',description='Same invoice Sales attributed by invoice-time role; never add Buyer and Bill-to totals.')
        add(role+' Sales Share %',f"DIVIDE([{role} Sales],CALCULATE([{role} Sales],ALLSELECTED('{table}')))",'Attribution','0.00%')
        add(role+' Customer Count',f"COUNTROWS(FILTER(VALUES('{table}'[source_customer_id]),[{role} Sales]<>BLANK()))",'Attribution','#,0')
        add(role+' Rank',f"IF(HASONEVALUE('{table}'[source_customer_id]),RANKX(ALLSELECTED('{table}'),[{role} Sales],,DESC,Dense))",'Attribution','#,0')
        add('Top N '+role+' Concentration %',f"VAR Population=ADDCOLUMNS(ALLSELECTED('{table}'),\"@Sales\",[{role} Sales]) RETURN DIVIDE(SUMX(TOPN([Selected Top N],Population,[@Sales],DESC,'{table}'[source_customer_id],ASC),[@Sales]),SUMX(Population,[@Sales]))",'Attribution','0.00%')
        add('Top 5 '+role+' Concentration %',f"VAR Population=ADDCOLUMNS(ALLSELECTED('{table}'),\"@Sales\",[{role} Sales]) RETURN DIVIDE(SUMX(TOPN(5,Population,[@Sales],DESC,'{table}'[source_customer_id],ASC),[@Sales]),SUMX(Population,[@Sales]))",'Attribution','0.00%')
        add('Top N '+role+' Sales',f'IF([{role} Rank]<=[Selected Top N],[{role} Sales])','Attribution')
    add('Selected Role Sales',"IF(SELECTEDVALUE(Role[Role],\"Buyer\")=\"Buyer\",CALCULATE([Buyer Sales],TREATAS(VALUES('Attribution Customer'[source_customer_id]),Buyer[source_customer_id])),CALCULATE([Bill-to Sales],TREATAS(VALUES('Attribution Customer'[source_customer_id]),'Bill-to'[source_customer_id])))",'Attribution')
    add('Selected Role Sales Share %',"DIVIDE([Selected Role Sales],CALCULATE([Selected Role Sales],ALLSELECTED('Attribution Customer')))",'Attribution','0.00%')
    add('Selected Role Rank',"IF(HASONEVALUE('Attribution Customer'[source_customer_id]),RANKX(ALLSELECTED('Attribution Customer'),[Selected Role Sales],,DESC,Dense))",'Attribution','#,0')
    for role,table in [('Buyer','Buyer'),('Bill-to','Bill-to')]:
        add(role+' Cumulative Share %',f"VAR N=MAX(1,COALESCE(MAX('Concentration Rank'[Value]),1)) VAR Population=ADDCOLUMNS(ALLSELECTED('{table}'),\"@Sales\",[{role} Sales]) VAR TopSales=SUMX(TOPN(N,Population,[@Sales],DESC,'{table}'[source_customer_id],ASC),[@Sales]) RETURN DIVIDE(TopSales,SUMX(Population,[@Sales]))",'Attribution','0.0%')
    add('Negative LineProfit Records',"CALCULATE([Eligible Invoice Lines],'Invoice Lines'[source_reported_line_profit]<0)",'Exceptions','#,0')
    add('Negative LineProfit Rate','DIVIDE([Negative LineProfit Records],[Eligible Invoice Lines])','Exceptions','0.00%')
    add('Negative Source LineProfit',"CALCULATE(SUM('Invoice Lines'[source_reported_line_profit]),'Invoice Lines'[source_reported_line_profit]<0,'Invoice Lines'[is_sales_eligible]=TRUE())",'Exceptions',description='Source-reported negative component, not certified losses, GP or COGS.')
    add('Affected Product Count',"CALCULATE(DISTINCTCOUNT('Invoice Lines'[source_stock_item_id]),'Invoice Lines'[source_reported_line_profit]<0,'Invoice Lines'[is_sales_eligible]=TRUE())",'Exceptions','#,0')
    add('Data Coverage Days',"COUNTROWS(VALUES('Date'[calendar_date]))",'Coverage','#,0')
    add('Zero-Transaction Days',"COUNTROWS(FILTER(VALUES('Date'[calendar_date]),COALESCE([Invoice Count],0)=0&&COALESCE([Order Count],0)=0))",'Coverage','#,0')
    add('Active Sales Days',"COUNTROWS(FILTER(VALUES('Date'[calendar_date]),[Invoice Count]>0))",'Coverage','#,0')
    add('Zero-Transaction Sundays',"COUNTROWS(FILTER(VALUES('Date'[calendar_date]),WEEKDAY('Date'[calendar_date],2)=7&&COALESCE([Invoice Count],0)=0&&COALESCE([Order Count],0)=0))",'Coverage','#,0')
    add('Orders with Direct Invoice',"VAR InvoicedOrders=CALCULATETABLE(VALUES(Invoices[source_order_id]),REMOVEFILTERS('Date'),Invoices[is_sales_eligible]=TRUE()) RETURN CALCULATE([Order Count],TREATAS(InvoicedOrders,Orders[source_order_id]))",'Coverage','#,0',description='Selected OrderDate cohort; direct invoice references across captured dates, not a fulfillment status.')
    add('Orders without Direct Invoice','[Order Count]-[Orders with Direct Invoice]','Coverage','#,0')
    add('Backorder Diagnostic Status','"BLOCKED: BackorderOrderID is absent from the 12 approved BI objects. Direct-link gap is not a fulfillment failure rate."','Narratives','')
    add('Coverage Narrative','"Observed calendar and source-profit diagnostics only. Zero-transaction Sundays are not missing data; negative source LineProfit is not certified accounting loss."','Narratives','')
    return output


def semantic_model():
    original=json.loads((ROOT/'.local/powerbi-sales-01/original-model.bim').read_text(encoding='utf-8-sig'))
    inventory=json.loads((ROOT/'.local/powerbi-sales-01/source-inventory.json').read_text())['objects']
    originals={t['name']:t for t in original['model']['tables']}
    selection={
      'dw_core.dim_date':('Date',['date_key','calendar_date','calendar_year','calendar_month','calendar_day','calendar_quarter','month_start','_capture_id','ruleset_version','measure_version']),
      'dw_core.dim_product':('Product',['product_key','source_stock_item_id','stock_item_name','brand','size','_capture_id']),
      'dw_core.dim_customer':('Buyer',['customer_key','source_customer_id','customer_name','_capture_id']),
      'dw_core.fact_invoice_line':('Invoice Lines',['source_invoice_line_id','source_invoice_id','source_order_id','invoice_date_key','invoice_date','source_buyer_customer_id','source_bill_to_customer_id','buyer_observed_customer_key','bill_to_observed_customer_key','source_stock_item_id','observed_product_key','quantity','invoiced_sales_before_tax','tax_amount','invoice_amount_including_tax','source_reported_line_profit','is_sales_eligible','has_warning','_capture_id','ruleset_version','measure_version']),
      'dw_intermediate.int_invoice_header':('Invoices',['source_invoice_id','source_order_id','invoice_date_key','source_buyer_customer_id','source_bill_to_customer_id','buyer_observed_customer_key','bill_to_observed_customer_key','is_sales_eligible','_capture_id']),
      'dw_intermediate.int_order_header':('Orders',['source_order_id','order_date_key','source_buyer_customer_id','buyer_observed_customer_key','is_order_eligible','_capture_id']),
    }
    tables=[]
    for source,(name,columns) in selection.items():
        schema,entity=source.split('.')
        old=originals.get(schema+' '+entity,{})
        oldcols={c['name']:c for c in old.get('columns',[])}
        actual=dict(inventory[source]['columns'])
        cols=[]
        for col in columns:
            assert col in actual,(source,col)
            kind=actual[col]
            data_type='dateTime' if kind=='date' else 'int64' if kind in ('integer','bigint') else 'boolean' if kind=='boolean' else 'decimal' if kind=='numeric' else 'string'
            item={'name':col,'dataType':data_type,'sourceColumn':col,'lineageTag':oldcols.get(col,{}).get('lineageTag',uid(name+'/'+col)),'summarizeBy':'none'}
            if data_type=='dateTime':item['formatString']='dd MMM yyyy'
            if data_type=='decimal':item['formatString']='#,0.00'
            item['isHidden']=col not in ('calendar_date','calendar_year','stock_item_name','brand','size','customer_name')
            cols.append(item)
        type_names={'dateTime':'type date','int64':'Int64.Type','boolean':'type logical','decimal':'Currency.Type','string':'type text'}
        mtypes=', '.join('{"'+c['name']+'", '+type_names[c['dataType']]+'}' for c in cols)
        selected=', '.join('"'+c+'"' for c in columns)
        expression=f'''let
    Source = PostgreSQL.Database("127.0.0.1:55434", "retail_raw", [CreateNavigationProperties=false]),
    Data = Source{{[Schema="{schema}",Item="{entity}"]}}[Data],
    Selected = Table.SelectColumns(Data, {{{selected}}}),
    VersionIDs = List.Distinct(Selected[_capture_id]),
    Pinned = if List.Count(VersionIDs) = 1 and Text.From(VersionIDs{{0}}) = "{PIN}" then Selected else error "Unexpected analytical version",
    Typed = Table.TransformColumnTypes(Pinned, {{{mtypes}}})
in
    Typed'''
        tables.append({'name':name,'lineageTag':old.get('lineageTag',uid(name)),
            'description':f'Imported from {source}; version {PIN}. Observed-current labels, not historical SCD2 attribution.',
            'columns':cols,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expression}}]})
    date=tables[0];date['dataCategory']='Time'
    next(c for c in date['columns'] if c['name']=='calendar_date')['isKey']=True
    for name,expr,kind in [('Year Month',"FORMAT('Date'[calendar_date],\"yyyy-MM\")",'string'),('Year Month Sort',"YEAR('Date'[calendar_date])*100+MONTH('Date'[calendar_date])",'int64'),('Quarter',"\"Q\"&'Date'[calendar_quarter]",'string'),('Weekday',"FORMAT('Date'[calendar_date],\"ddd\")",'string'),('Weekday Sort',"WEEKDAY('Date'[calendar_date],2)",'int64')]:
        date['columns'].append({'type':'calculated','name':name,'expression':expr,'dataType':kind,'isHidden':name.endswith('Sort'),'lineageTag':uid('Date/'+name),'summarizeBy':'none'})
    next(c for c in date['columns'] if c['name']=='Year Month')['sortByColumn']='Year Month Sort'
    next(c for c in date['columns'] if c['name']=='Weekday')['sortByColumn']='Weekday Sort'
    date['hierarchies']=[{'name':'Calendar','levels':[{'name':n,'ordinal':i,'column':c} for i,(n,c) in enumerate([('Year','calendar_year'),('Quarter','Quarter'),('Month','Year Month')])]}]
    def calc(name,expr,columns):
        tables.append({'name':name,'lineageTag':uid(name),'columns':[{'type':'calculatedTableColumn','name':c,'dataType':kind,'sourceColumn':'['+c+']','lineageTag':uid(name+'/'+c),'summarizeBy':'none'} for c,kind in columns],
            'partitions':[{'name':name,'source':{'type':'calculated','expression':expr}}]})
    calc('Bill-to','SELECTCOLUMNS(Buyer,"customer_key",Buyer[customer_key],"source_customer_id",Buyer[source_customer_id],"customer_name",Buyer[customer_name])',[('customer_key','string'),('source_customer_id','int64'),('customer_name','string')])
    calc('Attribution Customer','SELECTCOLUMNS(Buyer,"source_customer_id",Buyer[source_customer_id],"customer_name",Buyer[customer_name])',[('source_customer_id','int64'),('customer_name','string')])
    calc('Top N','GENERATESERIES(5,50,5)',[('Value','int64')])
    calc('Role','DATATABLE("Role",STRING,"Role Sort",INTEGER,{{"Buyer",1},{"Bill-to",2}})',[('Role','string'),('Role Sort','int64')])
    tables[-1]['columns'][0]['sortByColumn']='Role Sort';tables[-1]['columns'][1]['isHidden']=True
    calc('Ranking Basis','DATATABLE("Basis",STRING,{{"Sales"},{"Units"}})',[('Basis','string')])
    calc('Concentration Rank','VAR N=COALESCE(COUNTROWS(Buyer),0) RETURN FILTER(GENERATESERIES(1,MAX(1,N),1),[Value]<=N)',[('Value','int64')])
    calc('Decomposition','DATATABLE("Component",STRING,{{"Invoice volume"},{"AIV"},{"Interaction"}})',[('Component','string')])
    calc('Metrics','ROW("Placeholder",BLANK())',[('Placeholder','string')])
    tables[-1]['columns'][0]['isHidden']=True;tables[-1]['measures']=measures()
    for t in tables:
        if t['name'] in ('Invoices','Orders','Invoice Lines'):t['isHidden']=True
        if t['name'] in ('Bill-to','Attribution Customer'):
            for c in t['columns']:
                if c['name']!='customer_name':c['isHidden']=True
    relationships=[]
    for frm,col,to,key in [('Invoice Lines','invoice_date_key','Date','date_key'),('Invoices','invoice_date_key','Date','date_key'),('Orders','order_date_key','Date','date_key'),('Invoice Lines','observed_product_key','Product','product_key'),('Invoice Lines','buyer_observed_customer_key','Buyer','customer_key'),('Invoices','buyer_observed_customer_key','Buyer','customer_key'),('Orders','buyer_observed_customer_key','Buyer','customer_key'),('Invoice Lines','bill_to_observed_customer_key','Bill-to','customer_key'),('Invoices','bill_to_observed_customer_key','Bill-to','customer_key')]:
        relationships.append({'name':uid('relationship/'+frm+'/'+col),'fromTable':frm,'fromColumn':col,'toTable':to,'toColumn':key,'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True})
    return {'name':original['name'],'compatibilityLevel':1606,'model':{'culture':'en-US','dataAccessOptions':deepcopy(original['model'].get('dataAccessOptions',{})),'defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-US','discourageImplicitMeasures':True,'tables':tables,'relationships':relationships,'annotations':[{'name':'__PBI_TimeIntelligenceEnabled','value':'0'},{'name':'PBI_QueryOrder','value':json.dumps(list(selection_entry[0] for selection_entry in selection.values()))}]}}


def expr(value):
    literal='true' if value is True else 'false' if value is False else str(value)+'D' if isinstance(value,(int,float)) else "'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':literal}}}
def fill(value):return {'solid':{'color':expr(value)}}
def slicer_default(table,column,value):
    literal=str(value)+'L' if isinstance(value,int) else "'"+value.replace("'","''")+"'"
    return {'general':[{'properties':{'filter':{'Version':2,'From':[{'Name':'d','Entity':table,'Type':0}],
        'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'d'}},'Property':column}}],
                                   'Values':[[{'Literal':{'Value':literal}}]]}}}]}}}]}
def projection(table,column,measure=False):
    labels={'calendar_year':'Year','calendar_date':'Date','stock_item_name':'Product','customer_name':'Customer',
            'Product Lifetime Rank':'Lifetime Sales rank','Comparable-Period Product Rank':'Latest YTD Sales rank',
            'Product Active Months':'Active months','Product Rank Change':'Sales rank delta','Product Rank by Selected Basis':'Selected metric rank'}
    return {'field':{('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}},'queryRef':table+'.'+column,'nativeQueryRef':column,'displayName':labels.get(column,column)}


def report():
    pages=['01 | Sales Performance','02 | Product Contribution','03 | Sales Attribution','04 | Exceptions & Coverage']
    ids=[uid('page/'+n).replace('-','')[:20] for n in pages]
    original=HERE/'Sales_Dashboard.pbix'
    with zipfile.ZipFile(original) as z:
        for name in z.namelist():
            if name.startswith('Report/StaticResources/'):
                dest=REPORT/name.removeprefix('Report/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
        config=json.loads(z.read('Report/definition/report.json'))
        background=json.loads(z.read('Report/definition/pages/a3956bbc6d0002b35090/page.json'))['objects']
    theme_file=REPORT/'StaticResources/RegisteredResources/retail-theme.json'
    shutil.copyfile(HERE/'retail-theme.json',theme_file)
    package=next(p for p in config['resourcePackages'] if p['name']=='RegisteredResources')
    package['items'].append({'name':'retail-theme.json','path':'retail-theme.json','type':'CustomTheme'})
    config['themeCollection']['customTheme']={'name':'retail-theme.json','type':'RegisteredResources','reportVersionAtImport':{'visual':'2.14.0','report':'3.4.0','page':'2.3.1'}}
    write(REPORT/'definition/report.json',config)
    write(REPORT/'definition/pages/pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json','pageOrder':ids,'activePageName':ids[0]})
    base=REPORT/'definition/pages'
    # Remove only the empty CLI scaffold page, never Owner files or populated pages.
    for path in base.glob('*/page.json'):
        if path.parent.name not in ids:
            assert not (path.parent/'visuals').exists()
            path.unlink();path.parent.rmdir()
    specification=[]
    for index,(page_id,title) in enumerate(zip(ids,pages)):
        page={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json','name':page_id,'displayName':title,'width':1920,'height':1080,'displayOption':'FitToPage','objects':deepcopy(background)}
        visual_list=[]
        def visual(kind,title,x,y,w,h,roles=None,objects=None,sort=None):
            vid=uid(page_id+'/'+title).replace('-','')[:20]
            v={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json','name':vid,
               'position':{'x':x,'y':y,'z':len(visual_list)*1000,'width':w,'height':h,'tabOrder':len(visual_list)*1000},
               'visual':{'visualType':kind,'drillFilterOtherVisuals':True,
                   'visualContainerObjects':{'title':[{'properties':{'show':expr(True),'text':expr(title),'fontSize':expr(13),'fontColor':fill('#15273D')}}],
                     'background':[{'properties':{'show':expr(True),'color':fill('#FFFFFF'),'transparency':expr(8)}}],
                     'border':[{'properties':{'show':expr(False)}}]}}}
            v['visual']['visualContainerObjects']['subTitle']=[{'properties':{'show':expr(False)}}]
            if roles:
                v['visual']['query']={'queryState':{role:{'projections':[projection(*col) for col in columns]} for role,columns in roles.items()}}
            if sort:
                v['visual']['query']['sortDefinition']={'sort':[{'field':projection(*sort[0])['field'],'direction':sort[1]}],'isDefaultSort':False}
            if objects:v['visual']['objects']=objects
            if kind=='actionButton':
                v['visual'].setdefault('objects',{}).setdefault('text',[]).insert(0,{'properties':{'show':expr(True)}})
                v['visual']['objects']['icon']=[{'properties':{'show':expr(False)}}]
            if kind=='card':
                v['visual'].setdefault('objects',{})['categoryLabels']=[{'properties':{'show':expr(False)}}]
            write(base/page_id/'visuals'/vid/'visual.json',v)
            visual_list.append({'id':vid,'type':kind,'title':title,'position':v['position']})
            return vid
        for n,(target,label) in enumerate(zip(ids,['Performance','Products','Attribution','Exceptions'])):
            visual('actionButton',label,25,150+n*66,230,52,objects={
              'text':[{'selector':{'id':'default'},'properties':{'show':expr(True),'text':expr(label),'fontSize':expr(13),'fontColor':fill('#FFFFFF' if n==index else '#0B3158')}}],
              'fill':[{'selector':{'id':'default'},'properties':{'show':expr(True),'fillColor':fill('#0756A5' if n==index else '#E5EFF9')}}]})
            vpath=base/page_id/'visuals'/visual_list[-1]['id']/'visual.json';v=json.loads(vpath.read_text())
            v['visual']['visualContainerObjects']['visualLink']=[{'properties':{'show':expr(True),'type':expr('PageNavigation'),'navigationSection':expr(target)}}]
            v['visual']['visualContainerObjects']['title'][0]['properties']['show']=expr(False);write(vpath,v)
        reset=visual('actionButton','Clear slicers',25,970,230,45,objects={'text':[{'selector':{'id':'default'},'properties':{'show':expr(True),'text':expr('Clear slicers'),'fontSize':expr(12),'fontColor':fill('#0B3158')}}]})
        path=base/page_id/'visuals'/reset/'visual.json';v=json.loads(path.read_text());v['visual']['visualContainerObjects']['visualLink']=[{'properties':{'show':expr(True),'type':expr('ClearAllSlicers')}}];write(path,v)
        year_options={'data':[{'properties':{'mode':expr('Dropdown')}}]}
        if index==0:year_options.update(slicer_default('Date','calendar_year',2016))
        visual('slicer','Year',25,455,230,100 if index==1 else 150,{'Values':[(D,'calendar_year',False)]},year_options)
        visual('slicer','Date range',25,575 if index==1 else 625,230,140 if index==1 else 170,{'Values':[(D,'calendar_date',False)]},{'data':[{'properties':{'mode':expr('Between')}}]})
        if index==1:
            top_options={'data':[{'properties':{'mode':expr('Dropdown')}}],**slicer_default('Top N','Value',10)}
            visual('slicer','Top N',25,735,230,90,{'Values':[('Top N','Value',False)]},top_options)
            visual('slicer','Rank basis (detail)',25,845,230,90,{'Values':[('Ranking Basis','Basis',False)]},{'data':[{'properties':{'mode':expr('Dropdown')}}]})
        elif index==2:
            visual('slicer','Attribution role',25,815,230,110,{'Values':[('Role','Role',False)]},{'data':[{'properties':{'mode':expr('Dropdown')}}],'selection':[{'properties':{'strictSingleSelect':expr(True)}}],**slicer_default('Role','Role','Buyer')})
        # Generous content grid inside the Owner's 1920x1080 background.
        visual('textbox',title,300,110,1595,40,objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':title,'textStyle':{'fontFamily':'Segoe UI Semibold','fontSize':'15pt','color':'#0B3158'}}]}]}}]})
        titlepath=base/page_id/'visuals'/visual_list[-1]['id']/'visual.json'
        titlevisual=json.loads(titlepath.read_text());titlevisual['visual']['visualContainerObjects']['title'][0]['properties']['show']=expr(False)
        titlevisual['visual']['visualContainerObjects']['background'][0]['properties']['transparency']=expr(100);write(titlepath,titlevisual)
        cards=[['Total Sales Before Tax','Invoice Count','Average Invoice Value','Units Sold'],
               ['Distinct Active Products','Top 20% SKU Sales Share','SKUs for 80% Sales','Top N Ranking Overlap'],
               ['Top 5 Buyer Concentration %','Top 5 Bill-to Concentration %','Buyer Customer Count','Bill-to Customer Count'],
               ['Negative LineProfit Records','Negative LineProfit Rate','Affected Product Count','Zero-Transaction Sundays']][index]
        for n,measure in enumerate(cards):
            visual('card',measure,300+n*398,155,382,130,{'Values':[('Metrics',measure,True)]},
                   {'labels':[{'properties':{'fontSize':expr(28),'color':fill('#0B3158'),'labelDisplayUnits':expr(0)}}]})
        if index==0:
            visual('lineChart','Monthly Sales and comparable prior-year dates',300,305,975,300,{'Category':[(D,'Year Month',False)],'Y':[('Metrics','Total Sales Before Tax',True),('Metrics','Sales Previous Year Comparable Period',True)]},sort=((D,'Year Month',False),'Ascending'))
            visual('lineClusteredColumnComboChart','Invoice volume versus AIV — separate axes',1295,305,600,300,{'Category':[(D,'Year Month',False)],'Y':[('Metrics','Invoice Count',True)],'Y2':[('Metrics','Average Invoice Value',True)]},{'valueAxis':[{'properties':{'secShow':expr(True),'showAxisTitle':expr(True),'titleText':expr('Invoices'),'secShowAxisTitle':expr(True),'secTitleText':expr('AIV before tax')}}]})
            visual('columnChart','Exact Sales delta decomposition — not causal attribution',300,625,580,290,{'Category':[('Decomposition','Component',False)],'Y':[('Metrics','Sales Change Contribution',True)]})
            visual('pivotTable','Monthly Sales, volume and value',900,625,995,290,{'Rows':[(D,'Year Month',False)],'Values':[('Metrics',n,True) for n in ['Total Sales Before Tax','Invoice Count','Average Invoice Value','Units Sold','Sales YoY %','Invoice Count YoY %','AIV YoY %']]})
            visual('card','Selected-period interpretation',300,935,1595,90,{'Values':[('Metrics','Performance Narrative',True)]},{'labels':[{'properties':{'fontSize':expr(14)}}]})
        elif index==1:
            visual('lineClusteredColumnComboChart','Product Pareto — ranked Sales and cumulative contribution',300,305,975,295,{'Category':[(P,'stock_item_name',False)],'Y':[('Metrics','Product Sales',True)],'Y2':[('Metrics','Product Cumulative Sales %',True),('Metrics','Pareto Threshold',True)]},{'valueAxis':[{'properties':{'secShow':expr(True),'secStart':expr(0),'secEnd':expr(1),'secShowAxisTitle':expr(True),'secTitleText':expr('Cumulative share')}}]},sort=(('Metrics','Product Sales',True),'Descending'))
            visual('scatterChart','Source quantity versus invoiced value',1295,305,600,295,{'Category':[(P,'stock_item_name',False)],'X':[('Metrics','Product Units',True)],'Y':[('Metrics','Product Sales',True)],'Tooltips':[('Metrics','Product Sales per Unit',True),('Metrics','Product Active Months',True)]})
            visual('barChart','Top products by Sales',300,620,480,275,{'Category':[(P,'stock_item_name',False)],'Y':[('Metrics','Top N Product Sales',True)]},sort=(('Metrics','Top N Product Sales',True),'Descending'))
            visual('barChart','Top products by source Units',800,620,475,275,{'Category':[(P,'stock_item_name',False)],'Y':[('Metrics','Top N Product Units',True)]},sort=(('Metrics','Top N Product Units',True),'Descending'))
            visual('pivotTable','History-aware ranking — latest captured year YTD',1295,620,600,400,{'Rows':[(P,'stock_item_name',False)],'Values':[('Metrics',n,True) for n in ['Product Rank by Selected Basis','Product Lifetime Rank','Comparable-Period Product Rank','Product Active Months','Product Rank Change']]})
            visual('slicer','Product selection',300,915,975,110,{'Values':[(P,'stock_item_name',False)]},{'data':[{'properties':{'mode':expr('Dropdown')}}]})
        elif index==2:
            buyer=visual('barChart','Buyer Sales — independently ranked',300,305,780,305,{'Category':[(B,'customer_name',False)],'Y':[('Metrics','Top N Buyer Sales',True)]},sort=(('Metrics','Top N Buyer Sales',True),'Descending'))
            bill=visual('barChart','Bill-to Sales — same revenue, different attribution',1100,305,795,305,{'Category':[(BT,'customer_name',False)],'Y':[('Metrics','Top N Bill-to Sales',True)]},sort=(('Metrics','Top N Bill-to Sales',True),'Descending'))
            page['visualInteractions']=[{'source':buyer,'target':bill,'type':'NoFilter'},{'source':bill,'target':buyer,'type':'NoFilter'}]
            visual('lineChart','Cumulative concentration by number of customers',300,630,780,390,{'Category':[('Concentration Rank','Value',False)],'Y':[('Metrics','Buyer Cumulative Share %',True),('Metrics','Bill-to Cumulative Share %',True)]},sort=(('Concentration Rank','Value',False),'Ascending'))
            visual('pivotTable','Selected role detail — never add Buyer and Bill-to',1100,630,795,390,{'Rows':[('Attribution Customer','customer_name',False)],'Values':[('Metrics','Selected Role Sales',True),('Metrics','Selected Role Sales Share %',True),('Metrics','Selected Role Rank',True)]})
        else:
            visual('barChart','Negative source LineProfit lines by Product',300,305,780,290,{'Category':[(P,'stock_item_name',False)],'Y':[('Metrics','Negative LineProfit Records',True)]},sort=(('Metrics','Negative LineProfit Records',True),'Descending'))
            visual('lineClusteredColumnComboChart','Warning count and eligible invoice-line rate',1100,305,795,290,{'Category':[(D,'Year Month',False)],'Y':[('Metrics','Negative LineProfit Records',True)],'Y2':[('Metrics','Negative LineProfit Rate',True)]},{'valueAxis':[{'properties':{'secShow':expr(True),'secStart':expr(0),'secEnd':expr(1),'secShowAxisTitle':expr(True),'secTitleText':expr('Warning rate')}}]})
            visual('columnChart','Day-of-week activity — zero is not missing data',300,615,510,275,{'Category':[(D,'Weekday',False)],'Y':[('Metrics','Invoice Count',True),('Metrics','Order Count',True)]},sort=((D,'Weekday',False),'Ascending'))
            visual('pivotTable','Warning investigation — current Product and InvoiceDate',830,615,540,275,{'Rows':[(P,'stock_item_name',False),(D,'Year Month',False)],'Values':[('Metrics','Negative LineProfit Records',True),('Metrics','Negative LineProfit Rate',True)]})
            visual('pivotTable','Direct order references — not a fulfillment funnel',1390,615,505,275,{'Rows':[(D,'Year Month',False)],'Values':[('Metrics','Orders with Direct Invoice',True),('Metrics','Orders without Direct Invoice',True)]})
            visual('card','Backorder linkage requires separate approved data extension',300,910,1595,110,{'Values':[('Metrics','Backorder Diagnostic Status',True)]},{'labels':[{'properties':{'fontSize':expr(13)}}]})
        # Matrix levels require active projections; card/table projections do not.
        for entry in visual_list:
            path=base/page_id/'visuals'/entry['id']/'visual.json';v=json.loads(path.read_text())
            if v['visual']['visualType']=='pivotTable':
                for role,state in v['visual']['query']['queryState'].items():
                    for field in state['projections']:field['active']=True
                write(path,v)
        write(base/page_id/'page.json',page)
        specification.append({'id':page_id,'name':title,'visuals':visual_list})
    write(HERE/'page-specifications.json',specification)


def main():
    assert PROJECT.exists(),'Run official CLI scaffold first'
    MODEL.mkdir(exist_ok=True)
    write(MODEL/'definition.pbism',{'version':'4.0','settings':{}})
    write(MODEL/'model.bim',semantic_model())
    write(HERE/'measures.json',measures())
    (HERE/'measures.dax').write_text('\n\n'.join('// '+m['displayFolder']+' | '+m['description']+'\n'+m['name']+' =\n'+m['expression'] for m in measures())+'\n',encoding='utf-8')
    write(HERE/'retail-theme.json',{'name':'retail-theme.json','dataColors':['#0756A5','#008C95','#FF7900','#6D8EAD','#0B3158'],'background':'#F3F7FC','foreground':'#15273D','tableAccent':'#FF7900','textClasses':{'title':{'fontFace':'Segoe UI Semibold','fontSize':13,'color':'#15273D'},'callout':{'fontFace':'Segoe UI Semibold','fontSize':28,'color':'#0B3158'},'label':{'fontFace':'Segoe UI','fontSize':11,'color':'#15273D'}}})
    report()
    print(json.dumps({'status':'GENERATED_REQUIRES_RUNTIME_VALIDATION','measures':len(measures()),'pages':4}))


if __name__=='__main__':main()
