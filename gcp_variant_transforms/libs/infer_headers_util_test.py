# Copyright 2019 Google Inc.  All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for infer_headers_util module."""

from __future__ import absolute_import

from collections import OrderedDict
import unittest


from vcf.parser import _Format as Format
from vcf.parser import _Info as Info
from vcf.parser import field_counts

from gcp_variant_transforms.beam_io import vcf_header_io
from gcp_variant_transforms.beam_io import vcfio
from gcp_variant_transforms.libs import infer_headers_util


class InferHeaderUtilTest(unittest.TestCase):
  """Test case for `InferHeaderFields` DoFn."""

  def _get_sample_variant_1(self):
    variant = vcfio.Variant(
        reference_name='chr19', start=11, end=12, reference_bases='C',
        alternate_bases=['A', 'TT'], names=['rs1', 'rs2'], quality=2,
        filters=['PASS'],
        info={'IS': 'some data', 'ISI': '1', 'ISF': '1.0',
              'IF': 1.0, 'IB': True, 'IA': [1, 2]},
        calls=[vcfio.VariantCall(
            name='Sample1', genotype=[0, 1], phaseset='*',
            info={'FI': 20, 'FU': [10.0, 20.0]})]
    )
    return variant

  def _get_sample_variant_info_ia_cardinality_mismatch(self):
    variant = vcfio.Variant(
        reference_name='chr19', start=11, end=12, reference_bases='C',
        alternate_bases=['A', 'TT'], names=['rs1', 'rs2'], quality=2,
        filters=['PASS'],
        info={'IS': 'some data',
              'ISI': '1',
              'ISF': '1.0',
              'IF': 1.0,
              'IB': True,
              'IA': [0.1]},
        calls=[vcfio.VariantCall(
            name='Sample1', genotype=[0, 1], phaseset='*',
            info={'FI': 20, 'FU': [10.0, 20.0]})]
    )
    return variant

  def _get_sample_variant_info_ia_float_in_list(self):
    variant = vcfio.Variant(
        reference_name='chr19', start=11, end=12, reference_bases='C',
        alternate_bases=['A', 'TT'], names=['rs1', 'rs2'], quality=2,
        filters=['PASS'],
        info={'IS': 'some data',
              'ISI': '1',
              'ISF': '1.0',
              'IF': 1.0,
              'IB': True,
              'IA': [1, 0.2]},
        calls=[vcfio.VariantCall(
            name='Sample1', genotype=[0, 1], phaseset='*',
            info={'FI': 20, 'FU': [10.0, 20.0]})]
    )
    return variant

  def _get_sample_variant_info_ia_float_2_0_in_list(self):
    variant = vcfio.Variant(
        reference_name='chr19', start=11, end=12, reference_bases='C',
        alternate_bases=['A', 'TT'], names=['rs1', 'rs2'], quality=2,
        filters=['PASS'],
        info={'IS': 'some data',
              'ISI': '1',
              'ISF': '1.0',
              'IF': 1.0,
              'IB': True,
              'IA': [1, 2.0]},
        calls=[vcfio.VariantCall(
            name='Sample1', genotype=[0, 1], phaseset='*',
            info={'FI': 20, 'FU': [10.0, 20.0]})]
    )
    return variant

  def _get_sample_variant_format_fi_float_value(self):
    variant = vcfio.Variant(
        reference_name='chr19', start=11, end=12, reference_bases='C',
        alternate_bases=['A', 'TT'], names=['rs1', 'rs2'], quality=2,
        filters=['PASS'],
        info={'IS': 'some data',
              'ISI': '1',
              'ISF': '1.0',
              'IF': 1.0,
              'IB': True,
              'IA': [0.1, 0.2]},
        calls=[vcfio.VariantCall(
            name='Sample1', genotype=[0, 1], phaseset='*',
            info={'FI': 20.1, 'FU': [10.0, 20.0]})]
    )
    return variant

  def test_infer_mismatched_info_field_no_mismatches(self):
    variant = self._get_sample_variant_info_ia_float_2_0_in_list()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IF': Info('IF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', 'A', 'Integer', '', '', '')}
    corrected_info = infer_headers_util._infer_mismatched_info_field(
        'IA', variant.info.get('IA'),
        vcf_header_io.VcfHeader(infos=infos).infos.get('IA'),
        len(variant.alternate_bases))
    self.assertEqual(None, corrected_info)

  def test_infer_mismatched_info_field_correct_num(self):
    variant = self._get_sample_variant_info_ia_cardinality_mismatch()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IF': Info('IF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', -1, 'Float', '', '', '')}
    corrected_info = infer_headers_util._infer_mismatched_info_field(
        'IA', variant.info.get('IA'),
        vcf_header_io.VcfHeader(infos=infos).infos.get('IA'),
        len(variant.alternate_bases))
    expected = Info('IA', None, 'Float', '', '', '')
    self.assertEqual(expected, corrected_info)

  def test_infer_mismatched_info_field_correct_type(self):
    variant = self._get_sample_variant_info_ia_cardinality_mismatch()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IF': Info('IF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', None, 'Integer', '', '', '')}
    corrected_info = infer_headers_util._infer_mismatched_info_field(
        'IA', variant.info.get('IA'),
        vcf_header_io.VcfHeader(infos=infos).infos.get('IA'),
        len(variant.alternate_bases)
    )
    expected = Info('IA', None, 'Float', '', '', '')
    self.assertEqual(expected, corrected_info)

  def test_infer_mismatched_info_field_correct_type_list(self):
    variant = self._get_sample_variant_info_ia_float_in_list()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IF': Info('IF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', None, 'Integer', '', '', '')}
    corrected_info = infer_headers_util._infer_mismatched_info_field(
        'IA', variant.info.get('IA'),
        vcf_header_io.VcfHeader(infos=infos).infos.get('IA'),
        len(variant.alternate_bases)
    )
    expected = Info('IA', None, 'Float', '', '', '')
    self.assertEqual(expected, corrected_info)

  def test_infer_info_fields_no_conflicts(self):
    variant = self._get_sample_variant_1()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IF': Info('IF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', -1, 'Float', '', '', '')}
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), infer_headers=True)
    self.assertEqual({}, inferred_infos)

  def test_infer_info_fields_combined_conflicts(self):
    variant = self._get_sample_variant_info_ia_cardinality_mismatch()
    infos = {'IS': Info('IS', 1, 'String', '', '', ''),
             'ISI': Info('ISI', 1, 'Integer', '', '', ''),
             'ISF': Info('ISF', 1, 'Float', '', '', ''),
             'IB': Info('IB', 0, 'Flag', '', '', ''),
             'IA': Info('IA', -1, 'Integer', '', '', '')}
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), infer_headers=True)
    expected_infos = {'IF': Info('IF', 1, 'Float', '', '', ''),
                      'IA': Info('IA', None, 'Float', '', '', '')}
    self.assertEqual(expected_infos, inferred_infos)

  def test_infer_mismatched_format_field(self):
    variant = self._get_sample_variant_format_fi_float_value()
    formats = OrderedDict([
        ('FS', Format('FS', 1, 'String', 'desc')),
        ('FI', Format('FI', 2, 'Integer', 'desc')),
        ('FU', Format('FU', field_counts['.'], 'Float', 'desc')),
        ('GT', Format('GT', 2, 'Integer', 'Special GT key')),
        ('PS', Format('PS', 1, 'Integer', 'Special PS key'))])
    corrected_format = infer_headers_util._infer_mismatched_format_field(
        'FI', variant.calls[0].info.get('FI'),
        vcf_header_io.VcfHeader(formats=formats).formats.get('FI'))
    expected_formats = Format('FI', 2, 'Float', 'desc')
    self.assertEqual(expected_formats, corrected_format)

  def test_infer_format_fields_no_conflicts(self):
    variant = self._get_sample_variant_1()
    formats = OrderedDict([
        ('FS', Format('FS', 1, 'String', 'desc')),
        ('FI', Format('FI', 2, 'Integer', 'desc')),
        ('FU', Format('FU', field_counts['.'], 'Float', 'desc')),
        ('GT', Format('GT', 2, 'Integer', 'Special GT key')),
        ('PS', Format('PS', 1, 'Integer', 'Special PS key'))])
    header = infer_headers_util.infer_format_fields(
        variant, vcf_header_io.VcfHeader(formats=formats))
    self.assertEqual({}, header)

  def test_infer_format_fields_combined_conflicts(self):
    variant = self._get_sample_variant_format_fi_float_value()
    formats = OrderedDict([
        ('FS', Format('FS', 1, 'String', 'desc')),
        ('FI', Format('FI', 2, 'Integer', 'desc')),
        ('GT', Format('GT', 2, 'Integer', 'Special GT key')),
        ('PS', Format('PS', 1, 'Integer', 'Special PS key'))])
    inferred_formats = infer_headers_util.infer_format_fields(
        variant, vcf_header_io.VcfHeader(formats=formats))
    expected_formats = {'FI': Format('FI', 2, 'Float', 'desc'),
                        'FU': Format('FU', field_counts['.'], 'Float', '')}
    self.assertEqual(expected_formats, inferred_formats)

  def _get_annotation_infos(self):
    return OrderedDict([
        ('CSQ', Info(
            'CSQ',
            field_counts['.'],
            'String',
            'Annotations from VEP. Format: Allele|Gene|Position|Score',
            'src',
            'v')),
        ('IS', Info('I1', 1, 'String', 'desc', 'src', 'v')),
        ('ISI', Info('ISI', 1, 'Int', 'desc', 'src', 'v')),
        ('ISF', Info('ISF', 1, 'Float', 'desc', 'src', 'v')),
        ('IF', Info('IF', 1, 'Float', 'desc', 'src', 'v')),
        ('IB', Info('I1', 1, 'Flag', 'desc', 'src', 'v')),
        ('IA', Info('IA', field_counts['A'], 'Integer', 'desc', 'src', 'v'))])

  def _get_inferred_info(self, field, annotation, info_type):
    return Info(
        id='{0}_{1}_TYPE'.format(field, annotation),
        num=1,
        type=info_type,
        desc='Inferred type field for annotation {0}.'.format(annotation),
        source='',
        version='')

  def test_infer_annotation_empty_info(self):
    anno_fields = ['CSQ']
    infos = self._get_annotation_infos()
    variant = self._get_sample_variant_1()
    variant.info['CSQ'] = []
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), False, anno_fields)
    self.assertEqual({}, inferred_infos)

  def test_infer_annotation_types_no_conflicts(self):
    anno_fields = ['CSQ']
    infos = self._get_annotation_infos()
    variant = self._get_sample_variant_1()
    variant.info['CSQ'] = ['A|GENE1|100|1.2', 'TT|GENE1|101|1.3']
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), True, anno_fields)
    expected_infos = {
        'CSQ_Gene_TYPE': self._get_inferred_info('CSQ', 'Gene', 'String'),
        'CSQ_Position_TYPE':
            self._get_inferred_info('CSQ', 'Position', 'Integer'),
        'CSQ_Score_TYPE': self._get_inferred_info('CSQ', 'Score', 'Float')
    }
    self.assertDictEqual(expected_infos, inferred_infos)

  def test_infer_annotation_types_with_type_conflicts(self):
    anno_fields = ['CSQ']
    infos = self._get_annotation_infos()
    variant = self._get_sample_variant_1()
    variant.info['CSQ'] = ['A|1|100|1.2',
                           'A|2|101|1.3',
                           'A|1.2|start|0',
                           'TT|1.3|end|7']
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), False, anno_fields)

    expected_infos = {
        'CSQ_Gene_TYPE': self._get_inferred_info('CSQ', 'Gene', 'Float'),
        'CSQ_Position_TYPE':
            self._get_inferred_info('CSQ', 'Position', 'String'),
        'CSQ_Score_TYPE': self._get_inferred_info('CSQ', 'Score', 'Float')
    }
    self.assertDictEqual(expected_infos, inferred_infos)

  def test_infer_annotation_types_with_missing(self):
    anno_fields = ['CSQ']
    infos = self._get_annotation_infos()
    variant = self._get_sample_variant_1()
    variant.info['CSQ'] = ['A||100|',
                           'A||101|1.3',
                           'A|||1.4',
                           'TT|||']
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), False, anno_fields)
    expected_infos = {
        'CSQ_Gene_TYPE': self._get_inferred_info('CSQ', 'Gene', None),
        'CSQ_Position_TYPE':
            self._get_inferred_info('CSQ', 'Position', 'Integer'),
        'CSQ_Score_TYPE': self._get_inferred_info('CSQ', 'Score', 'Float')
    }
    self.assertDictEqual(expected_infos, inferred_infos)

  def test_infer_annotation_types_with_multiple_annotation_fields(self):
    anno_fields = ['CSQ', 'CSQ_VT']
    infos = self._get_annotation_infos()
    infos['CSQ_VT'] = Info(
        'CSQ_VT',
        -1,
        'String',
        'Annotations from VEP. Format: Allele|Gene|Position|Score',
        'source',
        'v')
    variant = self._get_sample_variant_1()
    variant.info['CSQ_VT'] = ['A|1|100|1.2',
                              'A|2|101|1.3']
    variant.info['CSQ'] = ['A|1|100|1.2',
                           'A|2|101|1.3']
    inferred_infos = infer_headers_util.infer_info_fields(
        variant, vcf_header_io.VcfHeader(infos=infos), False, anno_fields)
    expected_infos = {
        'CSQ_Gene_TYPE': self._get_inferred_info('CSQ', 'Gene', 'Integer'),
        'CSQ_Position_TYPE':
            self._get_inferred_info('CSQ', 'Position', 'Integer'),
        'CSQ_Score_TYPE': self._get_inferred_info('CSQ', 'Score', 'Float'),
        'CSQ_VT_Gene_TYPE':
            self._get_inferred_info('CSQ_VT', 'Gene', 'Integer'),
        'CSQ_VT_Position_TYPE':
            self._get_inferred_info('CSQ_VT', 'Position', 'Integer'),
        'CSQ_VT_Score_TYPE': self._get_inferred_info('CSQ_VT', 'Score', 'Float')
    }
    self.assertDictEqual(expected_infos, inferred_infos)
