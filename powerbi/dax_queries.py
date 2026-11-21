"""Generate actual-engine DAX validation queries; benchmarks remain independent SQL."""
import json
from pathlib import Path


def row(fields):
    return 'ROW('+','.join('"'+name+'",['+measure+']' for name,measure in fields.items())+')'


def main():
    baseline={'Sales':'Total Sales Before Tax','Tax':'Total Tax','IncludingTax':'Total Amount Including Tax',
              'Units':'Units Sold','Invoices':'Invoice Count','Orders':'Order Count','AIV':'Average Invoice Value',
              'Warnings':'Negative LineProfit Records','WarningRate':'Negative LineProfit Rate',
              'AffectedProducts':'Affected Product Count','Sundays':'Zero-Transaction Sundays',
              'Coverage':'Data Coverage Days','BuyerTop5':'Top 5 Buyer Concentration %',
              'BillToTop5':'Top 5 Bill-to Concentration %','BuyerCount':'Buyer Customer Count','BillToCount':'Bill-to Customer Count'}
    headline={k:baseline[k] for k in ('Sales','Invoices','Orders','AIV')}
    cases=[('baseline',row(baseline)),
           ('product_diagnostics',row({'Products':'Distinct Active Products','Top20Share':'Top 20% SKU Sales Share','SKUs80':'SKUs for 80% Sales','Top10Overlap':'Top N Ranking Overlap'}))]
    previous={'Sales':'Total Sales Before Tax','PY':'Sales Previous Year Comparable Period','SalesYoY':'Sales YoY %',
              'InvoiceYoY':'Invoice Count YoY %','AIVYoY':'AIV YoY %','YTD':'Sales YTD','PY_YTD':'Prior Year Comparable YTD',
              'Volume':'Volume Contribution','AIVComponent':'AIV Contribution','Interaction':'Interaction Contribution'}
    cases.append(('2016_comparable','CALCULATETABLE('+row(previous)+",'Date'[calendar_year]=2016)"))
    cases.append(('monthly',"SUMMARIZECOLUMNS('Date'[Year Month],"+','.join('"'+k+'",['+v+']' for k,v in headline.items())+") ORDER BY 'Date'[Year Month]"))
    cases.append(('single_month','CALCULATETABLE('+row(headline)+",'Date'[Year Month]=\"2016-05\")"))
    cases.append(('full_year','CALCULATETABLE('+row(headline)+",'Date'[calendar_year]=2015)"))
    cases.append(('product_222_rank',"FILTER(SUMMARIZECOLUMNS(Product[source_stock_item_id],\"Lifetime\",[Product Lifetime Rank],\"Comparable\",[Comparable-Period Product Rank],\"ActiveMonths\",[Product Active Months]),Product[source_stock_item_id]=222)"))
    cases.append(('product_single','CALCULATETABLE('+row(headline)+',Product[source_stock_item_id]=222)'))
    cases.append(('product_multi','CALCULATETABLE('+row(headline)+',TREATAS({222,223},Product[source_stock_item_id]))'))
    cases.append(('buyer_billto',row({'BuyerSales':'Buyer Sales','BillToSales':'Bill-to Sales'})))
    cases.append(('topn5','CALCULATETABLE('+row({'TopN':'Selected Top N','BuyerConcentration':'Top N Buyer Concentration %','BillToConcentration':'Top N Bill-to Concentration %'})+",'Top N'[Value]=5)"))
    cases.append(('role_detail_billto','CALCULATETABLE('+row({'AttributedSales':'Selected Role Sales'})+',Role[Role]="Bill-to")'))
    cases.append(('empty_period','CALCULATETABLE('+row({'Sales':'Total Sales Before Tax','Invoices':'Invoice Count','AIV':'Average Invoice Value','YoY':'Sales YoY %'})+",TREATAS({DATE(2026,1,1)},'Date'[calendar_date]))"))
    cases.append(('no_comparison_multi_year',row({'YoY':'Sales YoY %','Decomposition':'Interaction Contribution'})))
    cases.append(('direct_references',row({'Direct':'Orders with Direct Invoice','WithoutDirect':'Orders without Direct Invoice'})))
    out=[{'id':key,'dax':'EVALUATE '+dax} for key,dax in cases]
    Path(__file__).with_name('dax-validation-queries.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print('DAX_VALIDATION_QUERIES_READY',len(out))


if __name__=='__main__':main()
